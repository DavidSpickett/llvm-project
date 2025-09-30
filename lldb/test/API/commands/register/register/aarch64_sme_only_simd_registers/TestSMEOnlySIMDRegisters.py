"""
Check reading and writing of SIMD registers on a system that only has SME. Which
means that the "SVE" registers are only active during streaming mode.
"""

# TODO: rename this to TestSMEOnlyRegisters.py

from enum import Enum
import lldb
from lldbsuite.test.decorators import *
from lldbsuite.test.lldbtest import *
from lldbsuite.test import lldbutil
from itertools import cycle


class Mode(Enum):
    SIMD = 0
    SSVE = 2


class ByteVector(object):
    def __init__(self, data):
        self.data = data

    def __repr__(self):
        return "{" + " ".join([f'0x{b:02x}' for b in self.data]) + "}"

    def as_bytes(self):
        return self.data


class HexValue(object):
    def __init__(self, value, size):
        self.value = value
        # In bytes
        self.size = size

    def __repr__(self):
        return f"0x{self.value:0{self.size*2}x}"

    def as_bytes(self):
        data = []
        v = self.value
        # Little endian order.
        for i in range(self.size):
           data.append(v & 0xFF)
           v >>= 8 
        
        return data


class SVESIMDRegistersTestCase(TestBase):
    def get_build_flags(self, mode):
        # TODO: put these in the makefile instead
        # The memset provided by glibc may use instructions we cannot use in
        # streaming mode.
        cflags = "-march=armv8-a+sve+sme+sme2 -fno-builtin-memset"
        if mode == Mode.SSVE:
            cflags += " -DSSVE"
        # else we want SIMD mode, which processes start up in already.

        return {"CFLAGS_EXTRAS": cflags}

    def skip_if_needed(self, mode):
        if self.isAArch64SVE():
            self.skipTest("SVE must not be present outside of streaming mode.")

        if (mode == Mode.SSVE) and not self.isAArch64SME():
            self.skipTest(
                "SSVE registers must be supported."
            )

    def reg_names(self, prefix, count):
        return [f'{prefix}{n}' for n in range(count)]

    def expected_fpr_control(self):
        return [("fpsr", HexValue(0x50000015, 4)), ("fpcr", HexValue(0x05551505, 4))]

    def expected_registers_simd(self, svl_b):
        register_values = []

        # V regs are {N <7 0s> N <7 0s>} because we set the bottom element to N
        # where N is 1 + the register index.
        v_values = [ByteVector([n+1] + [0] * 7 + [n+1] + [0] * 7) for n in range(32)]
        register_values += list(zip(self.reg_names('v', 32), v_values, strict=True))

        register_values += self.expected_fpr_control()

        # Z regs are {N <7 0s> N <7 0s> <16 more 0s}. First half overlaps a V
        # register, the second half we fake 0s for as there is no real Z register
        # in non-streaming mode.
        z_values = [ByteVector([n+1] + [0] * 7 + [n+1] + [0] * 7 + [0] * (svl_b - 16)) for n in range(32)]
        register_values += list(zip(self.reg_names('z', 32), z_values, strict=True))

        # P regs are {<4 0s>}, we fake the value.
        p_values = [ByteVector([0]*(svl_b // 8)) for _ in range(16)]
        register_values += list(zip(self.reg_names('p', 16), p_values, strict=True))

        # ffr is all 0s, again a fake value.
        register_values += [("ffr", ByteVector([0]*(svl_b // 8)))]

        register_values += [
            # SVCR shows that ZA and streaming mode are off.
            ('svcr', HexValue(0, 8)),
            # SVG is the streaming vector length in granules.
            ('svg', HexValue(svl_b // 8, 8)),
        ]

        # ZA is being faked so is all 0s it is a square with svl_b sides.
        register_values += [('za', ByteVector([0x0]*(svl_b*svl_b)))]

        # TODO: don't check this if we don't have SME2
        # Fake zt0.
        register_values += [('zt0', ByteVector([0x00]*(svl_b*2)))]

        return dict(register_values)

    def expected_registers_streaming(self, svl_b):
        register_values = []

        # Streaming SVE registers have their elements set to their number plus 1.
        # So z0 has elements of 0x01, z1 is 0x02 and so on.
        v_values = [ByteVector([n+1]*16) for n in range(32)]
        register_values += list(zip(self.reg_names('v', 32), v_values, strict=True))

        register_values += self.expected_fpr_control() 

        z_values = [ByteVector([n+1]*svl_b) for n in range(32)]
        register_values += list(zip(self.reg_names('z', 32), z_values, strict=True))

        # P registers have all emlements set to the same value and that value
        # cycles between 0xff, 0x55, 0x11, 0x01 and 0x00.
        p_values = []
        for i, v in zip(range(16), cycle([0xff, 0x55, 0x11, 0x01, 0x00])):
            p_values.append(ByteVector([v]*(svl_b // 8)))

        register_values += list(zip(self.reg_names('p', 16), p_values, strict=True))

        # ffr is all 0s.
        register_values += [("ffr", ByteVector([0]*(svl_b // 8)))]

        register_values += [
            # Streaming mode and ZA are on.
            ('svcr', HexValue(0x3, 8)),
            # SVG is the streaming vector length in granules.
            ('svg', HexValue(svl_b // 8, 8)),
        ]

        register_values += [('za', ByteVector(list(range(1, svl_b+1)) * svl_b))]

        # TODO: don't check this if we don't have SME2
        register_values += [('zt0', ByteVector(list(range(1, (svl_b*2)+1))))]

        return dict(register_values)

    def setup_test(self, mode):
        self.skip_if_needed(mode)

        self.build(dictionary=self.get_build_flags(mode))
        self.line = line_number("main.c", "// Set a break point here.")

        exe = self.getBuildArtifact("a.out")
        self.runCmd("file " + exe, CURRENT_EXECUTABLE_SET)

        lldbutil.run_break_set_by_file_and_line(
            self, "main.c", self.line, num_expected_locations=1
        )
        self.runCmd("run", RUN_SUCCEEDED)

        self.expect(
            "thread backtrace",
            STOPPED_DUE_TO_BREAKPOINT,
            substrs=["stop reason = breakpoint 1."],
        )

    def get_svl_b(self):
        return self.dbg.GetSelectedTarget().GetProcess().GetSelectedThread().GetFrameAtIndex(0).FindRegister('vg').GetValueAsUnsigned() * 8

    def check_expected_regs_fn(self, expected_registers):
        def check_expected_regs():
            self.expect(f'register read {" ".join(expected_registers.keys())}',
                    substrs=[f"{n} = {v}" for n, v in expected_registers.items()])
        return check_expected_regs

    def write_expected_reg_data(self, reg_data, write_streaming, write_za):
        # Write expected register values into program memory so it can be
        # verified in-process.
        # This must be done via. memory write instead of expressions because
        # the latter may try to save/restore registers, which is part of what
        # this file tests so we can't rely on it here.

        # dict_keys(['v0', 'v1', 'v2', 'v3', 'v4', 'v5', 'v6', 'v7', 'v8', 'v9'
        # 'v10', 'v11', 'v12', 'v13', 'v14', 'v15', 'v16', 'v17', 'v18', 'v19'
        # 'v20', 'v21', 'v22', 'v23', 'v24', 'v25', 'v26', 'v27', 'v28', 'v29'
        # 'v30', 'v31', 'fpsr', 'fpcr', 'z0', 'z1', 'z2', 'z3', 'z4', 'z5', 'z6'
        # 'z7', 'z8', 'z9', 'z10', 'z11', 'z12', 'z13', 'z14', 'z15', 'z16', 'z17'
        # 'z18', 'z19', 'z20', 'z21', 'z22', 'z23', 'z24', 'z25', 'z26', 'z27'
        # 'z28', 'z29', 'z30', 'z31', 'p0', 'p1', 'p2', 'p3', 'p4', 'p5', 'p6'
        # 'p7', 'p8', 'p9', 'p10', 'p11', 'p12', 'p13', 'p14', 'p15', 'ffr',
        # 'svcr', 'svg', 'za', 'zt0'])

        for reg, value in reg_data.items():
            sym_name = None
            # Since we cannot expression evaluate, we have to manually offset
            # arrays.
            offset = 0

            # Offsets for scalable registers assume that the expected register
            # data length matches the current svl. 
            if reg.startswith('v'):
                num = reg.split('v')[1]
                offset = 16 * num
                sym_name = "expected_v_regs"
            elif reg == 'fpcr':
                sym_name = "expected_fpcr"
            elif reg == 'fpsr':
                sym_name = "expected_fpsr"
            elif reg.startswith('z'):
                num = reg.split('z')[1]
                offset = len(value.as_bytes()) * num
                sym_name = "expected_sve_z"
            elif reg.startswith('p'):
                num = reg.split('p')[1]
                offset = len(value.as_bytes()) * num
                sym_name = "expected_sve_p"
            elif reg == 'ffr':
                sym_name = "expected_sve_ffr"
            elif reg == 'za':
               sym_name = "expected_za"
            elif reg == 'zt0':
                sym_name = "expected_zt0"
            elif reg == "svcr":
                sym_name = "expected_svcr"
            elif reg == "svg":
                sym_name = "expected_svg"

            if sym_name is None:
                raise RuntimeError(f"Do not know how to write expected values for register {reg}.")

            address = self.lookup_address(sym_name)
            process = self.dbg.GetSelectedTarget().GetProcess()
            err = lldb.SBError()
            wrote = process.WriteMemory(address, bytearray(value.as_bytes()), err)
            self.assertTrue(err.Success())
            self.assertEqual(len(value.as_bytes()), wrote)

    # TODO: memoise? maybe not because it's used for multiple tests?
    def lookup_address(self, sym_name):
        target = self.dbg.GetSelectedTarget()
        # TODO: assert that module 0 is in fact the test program
        module = target.module[0]

        sym = module.FindSymbol(sym_name)
        self.assertTrue(sym.IsValid())
        address = sym.GetStartAddress().GetLoadAddress(target)

        # Dereference this pointer and return that.
        err = lldb.SBError()
        ptr = target.GetProcess().ReadPointerFromMemory(address, err)
        self.assertTrue(err.Success())
        
        return ptr

#    @no_debug_info_test
#    @skipIf(archs=no_match(["aarch64"]))
#    @skipIf(oslist=no_match(["linux"]))
#    def test_simd_registers_ssve(self):
#        self.setup_test(Mode.SSVE)
#        svl_b = self.get_svl_b()
#
#        expected_registers = self.expected_registers_streaming(svl_b)
#        check_expected_regs = self.check_expected_regs_fn(expected_registers)
#
#        check_expected_regs()
#
#        # Write via Z0
#        z_value = ByteVector([0x12]*svl_b)
#        self.runCmd(f'register write z0 "{z_value}"')
#
#        # z0 and v0 should change but nothing else.
#        expected_registers['z0'] = z_value
#        expected_registers['v0'] = ByteVector([0x12]*16) 
#
#        check_expected_regs()
#
#        # We can do the same via a V register, the value will be extended and sent as
#        # a Z write.
#        v_value = ByteVector([0x34]*16)
#        self.runCmd(f'register write v1 "{v_value}"')
#
#        # The lower half of z1 is the v value, the upper part is the 0x2 that was previously in there.
#        expected_registers['z1'] = ByteVector([0x34]*16 + [0x02]*(svl_b - 16))
#        expected_registers['v1'] = v_value 
#
#        check_expected_regs()
#
#        # Even though you can't set all these bits in reality, until we do
#        # a step, it'll seem like we did.
#        fpcontrol = "0xaaaaaaaa"
#
#        self.runCmd(f'register write fpsr {fpcontrol}')
#        expected_registers['fpsr'] = fpcontrol
#
#        check_expected_regs()
#
#        self.runCmd(f'register write fpcr {fpcontrol}')
#        expected_registers['fpcr'] = fpcontrol
#
#        check_expected_regs()
#
#        p_value = ByteVector([0x65] * (svl_b // 8))
#        self.expect(f'register write p0 "{p_value}"')
#        expected_registers['p0'] = p_value
#
#        check_expected_regs()
#
#        ffr_value = ByteVector([0x78] * (svl_b // 8))
#        self.expect(f'register write ffr "{ffr_value}"')
#        expected_registers['ffr'] = ffr_value
#        
#        check_expected_regs()
#
#        za_value = ByteVector(list(range(2, svl_b+2)) * svl_b)
#        self.expect(f'register write za "{za_value}"')
#        expected_registers['za'] = za_value
#
#        check_expected_regs()
#
#        # TODO: only do this for SME2
#        zt0_value = ByteVector(list(range(2, (svl_b*2)+2)))
#        self.expect(f'register write zt0 "{zt0_value}"')
#        expected_registers['zt0'] = zt0_value
#
#        check_expected_regs()

    @no_debug_info_test
    @skipIf(archs=no_match(["aarch64"]))
    @skipIf(oslist=no_match(["linux"]))
    def test_simd_registers_simd(self):
        self.setup_test(Mode.SIMD)
        svl_b = self.get_svl_b()

        expected_registers = self.expected_registers_simd(svl_b)
        check_expected_regs = self.check_expected_regs_fn(expected_registers)

        self.write_expected_reg_data(expected_registers, False, False)

        check_expected_regs()

        # In SIMD mode if you write Z0, only the parts that overlap V0 will
        # change.
        z_value = ByteVector([0x12]*svl_b)
        self.runCmd(f'register write z0 "{z_value}"')

        # z0 and z0 should change but nothing else. We check the rest because
        # we are faking Z register data in this mode, and any offset mistake
        # could lead to modifying other registers.
        expected_registers['z0'] = ByteVector([0x12]*16 + [0x00]*(svl_b - 16))
        expected_registers['v0'] = ByteVector([0x12]*16)

        # Write back to program so it can verify the values.
        # self.write_expected_reg_data(expected_registers, False, False)
        
        # TODO: step program so it can verify values

        # Check that debugger sees the values too.
        check_expected_regs()

        # We can do the same via a V register, the value will be extended and sent as
        # a Z write.
        v_value = ByteVector([0x34]*16)
        self.runCmd(f'register write v1 "{v_value}"')

        expected_registers['z1'] = ByteVector([0x34]*16 + [0x00]*(svl_b - 16))
        expected_registers['v1'] = v_value

        check_expected_regs()

        # FPSR and FPCR are still described as real registers, so they are
        # sent as normal writes.
        # Even though you can't set all these bits in reality, until we do
        # a step, it'll seem like we did.
        fpcontrol = "0xaaaaaaaa"

        # First FPSR on its own.
        self.runCmd(f'register write fpsr {fpcontrol}')
        expected_registers['fpsr'] = fpcontrol

        check_expected_regs()

        # Then FPCR.
        self.runCmd(f'register write fpcr {fpcontrol}')
        expected_registers['fpcr'] = fpcontrol

        check_expected_regs()

        # We are faking SVE registers while outside of streaming mode, and
        # predicate registers and ffr have no real register to overlay.
        # We chose to make this an error instead of eating the write silently.

        value = ByteVector([0x98]*(svl_b // 8))
        self.expect(f'register write p0 "{value}"', error=True)
        check_expected_regs()
        self.expect(f'register write ffr "{value}"', error=True)
        check_expected_regs()

        # Writing ZA or ZT0 would take us into streaming mode. This transition
        # is tested in the SVE+SME tests.

# Expression test combinations:
# Input state:
# * streaming mode on or off
# * ZA on or off
# * vector length

#    @no_debug_info_test
#    @skipIf(archs=no_match(["aarch64"]))
#    @skipIf(oslist=no_match(["linux"]))
#    def test_expr_simd_to_streaming(self):
#        # TODO: this test requires that you have streaming mode too!!!
#        self.setup_test(Mode.SIMD)
#        svl_b = self.get_svl_b()
# 
#        expected_registers = self.expected_registers_simd(svl_b)
#        check_expected_regs = self.check_expected_regs_fn(expected_registers)
# 
#        check_expected_regs()
#        self.expect("expression expr_enter_streaming_mode()")
#        check_expected_regs()

#    @no_debug_info_test
#    @skipIf(archs=no_match(["aarch64"]))
#    @skipIf(oslist=no_match(["linux"]))
#    def test_expr_simd_to_streaming(self):
#        self.setup_test(Mode.SSVE)
#        svl_b = self.get_svl_b()
# 
#        expected_registers = self.expected_registers_streaming(svl_b)
#        check_expected_regs = self.check_expected_regs_fn(expected_registers)
# 
#        check_expected_regs()
#        self.expect("expression expr_exit_streaming_mode()")
#        check_expected_regs()


    # TODO: check streaming to streaming expression, and non-streaming to non-streaming, including ZA on and off.
    # TODO: check restoring only ZA without disturbing anything else.