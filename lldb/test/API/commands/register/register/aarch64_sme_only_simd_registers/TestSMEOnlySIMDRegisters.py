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

    def __str__(self):
        return "streaming" if self == Mode.SSVE else "simd"

class ZA(Enum):
    ON = 1
    OFF = 2

    def __str__(self):
        return "on" if self == ZA.ON else "off"


class ByteVector(object):
    def __init__(self, data):
        self.data = data

    def __repr__(self):
        return "{" + " ".join([f'0x{b:02x}' for b in self.data]) + "}"

    def as_bytes(self):
        return self.data


class HexValue(object):
    # Assume all values are 64-bit, but some display as 32-bit, like fpcr.
    def __init__(self, value, repr_size=8):
        self.value = value
        # In bytes
        self.repr_size = repr_size

    def __repr__(self):
        v = self.value & ((1 << (self.repr_size*8)) - 1)
        return f"0x{v:0{self.repr_size*2}x}"

    def as_bytes(self):
        data = []
        v = self.value
        # Little endian order.
        for i in range(8):
           data.append(v & 0xFF)
           v >>= 8 
        
        return data


class SVESIMDRegistersTestCase(TestBase):
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
        return [("fpsr", HexValue(0x50000015, repr_size=4)), ("fpcr", HexValue(0x05551505, repr_size=4))]

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
            ('svcr', HexValue(0)),
            # SVG is the streaming vector length in granules.
            ('svg', HexValue(svl_b // 8)),
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
            ('svcr', HexValue(0x3)),
            # SVG is the streaming vector length in granules.
            ('svg', HexValue(svl_b // 8)),
        ]

        register_values += [('za', ByteVector(list(range(1, svl_b+1)) * svl_b))]

        # TODO: don't check this if we don't have SME2
        register_values += [('zt0', ByteVector(list(range(1, (svl_b*2)+1))))]

        return dict(register_values)

    def setup_test(self, mode, za):
        self.skip_if_needed(mode)

        self.build()
        self.line = line_number("main.c", "// Set a break point here.")

        exe = self.getBuildArtifact("a.out")
        self.runCmd("file " + exe, CURRENT_EXECUTABLE_SET)

        self.runCmd(f"settings set target.run-args {mode} {za}")

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

    def write_expected_reg_data(self, reg_data):
        # Write expected register values into program memory so it can be
        # verified in-process.
        # This must be done via. memory write instead of expressions because
        # the latter may try to save/restore registers, which is part of what
        # this file tests so we can't rely on it here.
        # We will always write Z and ZA/ZTO, it's up to the program whether it
        # checks them.

        for reg, value in reg_data.items():
            sym_name = None
            # Since we cannot expression evaluate, we have to manually offset
            # arrays.
            offset = 0

            # Offsets for scalable registers assume that the expected register
            # data length matches the current svl. 
            if reg == 'fpcr':
                sym_name = "expected_fpcr"
            elif reg == 'fpsr':
                sym_name = "expected_fpsr"
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
            elif reg.startswith('v'):
                num = int(reg.split('v')[1])
                offset = 16 * num
                sym_name = "expected_v_regs"
            elif reg.startswith('z'):
                num = int(reg.split('z')[1])
                offset = len(value.as_bytes()) * num
                sym_name = "expected_sve_z"
            elif reg.startswith('p'):
                num = int(reg.split('p')[1])
                offset = len(value.as_bytes()) * num
                sym_name = "expected_sve_p"

            if sym_name is None:
                raise RuntimeError(f"Do not know how to write expected values for register {reg}.")

            address = self.lookup_address(sym_name) + offset
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

    @no_debug_info_test
    @skipIf(archs=no_match(["aarch64"]))
    @skipIf(oslist=no_match(["linux"]))
    def test_simd_registers_ssve(self):
        self.setup_test(Mode.SSVE, ZA.ON)
        svl_b = self.get_svl_b()

        expected_registers = self.expected_registers_streaming(svl_b)
        check_expected_regs = self.check_expected_regs_fn(expected_registers)

        self.write_expected_reg_data(expected_registers)
        self.expect("next", substrs=["stop reason = step over"])
        check_expected_regs()

        # Write via Z0
        z_value = ByteVector([0x12]*svl_b)
        self.runCmd(f'register write z0 "{z_value}"')

        # z0 and v0 should change but nothing else.
        expected_registers['z0'] = z_value
        expected_registers['v0'] = ByteVector([0x12]*16) 
        
        self.write_expected_reg_data(expected_registers)
        self.expect("next", substrs=["stop reason = step over"])
        check_expected_regs()

        # We can do the same via a V register, the value will be extended and sent as
        # a Z write.
        v_value = ByteVector([0x34]*16)
        self.runCmd(f'register write v1 "{v_value}"')

        # The lower half of z1 is the v value, the upper part is the 0x2 that was previously in there.
        expected_registers['z1'] = ByteVector([0x34]*16 + [0x02]*(svl_b - 16))
        expected_registers['v1'] = v_value 

        self.write_expected_reg_data(expected_registers)
        self.expect("next", substrs=["stop reason = step over"])
        check_expected_regs()

        # Even though you can't set all these bits in reality, until we do
        # a step, it'll seem like we did.
        # This arbitrary value is 0x55...55 when written to the real register.
        # Some bits cannot be set.
        fpsr = HexValue(0xa800008a, repr_size=4)

        self.runCmd(f'register write fpsr {fpsr}')
        expected_registers['fpsr'] = fpsr 

        self.write_expected_reg_data(expected_registers)
        self.expect("next", substrs=["stop reason = step over"])
        check_expected_regs()

        # Again this is 0x55...55, but with bits we cannot set removed.
        fpcr = HexValue(0x05551505, repr_size=4)
        self.runCmd(f'register write fpcr {fpcr}')
        expected_registers['fpcr'] = fpcr

        self.write_expected_reg_data(expected_registers)
        self.expect("next", substrs=["stop reason = step over"])
        check_expected_regs()

        p_value = ByteVector([0x65] * (svl_b // 8))
        self.expect(f'register write p0 "{p_value}"')
        expected_registers['p0'] = p_value

        self.write_expected_reg_data(expected_registers)
        self.expect("next", substrs=["stop reason = step over"])
        check_expected_regs()

        # We cannot interact with ffr in streaming mode while in process. So this
        # will be verified by ptrace only.
        ffr_value = ByteVector([0x78] * (svl_b // 8))
        self.expect(f'register write ffr "{ffr_value}"')
        expected_registers['ffr'] = ffr_value

        # It will appear as if we wrote ffr, but in streaming mode without
        # SME_FA64+SVE, it essentially does not exist. 
        check_expected_regs()

        # At least make sure we didn't disturb anything else.
        self.write_expected_reg_data(expected_registers)
        self.expect("next", substrs=["stop reason = step over"])

        # The kernel will always return 0s for ffr.
        expected_registers['ffr'] = ByteVector([0x0] * (svl_b // 8))
        check_expected_regs()
        
        za_value = ByteVector(list(range(2, svl_b+2)) * svl_b)
        self.expect(f'register write za "{za_value}"')
        expected_registers['za'] = za_value

        self.write_expected_reg_data(expected_registers)
        self.expect("next", substrs=["stop reason = step over"])
        check_expected_regs()

        # # TODO: only do this for SME2
        zt0_value = ByteVector(list(range(2, (svl_b*2)+2)))
        self.expect(f'register write zt0 "{zt0_value}"')
        expected_registers['zt0'] = zt0_value

        self.write_expected_reg_data(expected_registers)
        self.expect("next", substrs=["stop reason = step over"])
        check_expected_regs()

    @no_debug_info_test
    @skipIf(archs=no_match(["aarch64"]))
    @skipIf(oslist=no_match(["linux"]))
    def test_simd_registers_simd(self):
        self.setup_test(Mode.SIMD, ZA.OFF)
        svl_b = self.get_svl_b()

        # Check for the values the program should have set.
        expected_registers = self.expected_registers_simd(svl_b)
        check_expected_regs = self.check_expected_regs_fn(expected_registers)

        self.write_expected_reg_data(expected_registers)
        self.expect("next", substrs=["stop reason = step over"])
        
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

        self.write_expected_reg_data(expected_registers)
        self.expect("next", substrs=["stop reason = step over"])
        
        check_expected_regs()

        # We can do the same via a V register, the value will be extended and sent as
        # a Z write.
        v_value = ByteVector([0x34]*16)
        self.runCmd(f'register write v1 "{v_value}"')

        expected_registers['z1'] = ByteVector([0x34]*16 + [0x00]*(svl_b - 16))
        expected_registers['v1'] = v_value

        self.write_expected_reg_data(expected_registers)
        self.expect("next", substrs=["stop reason = step over"])
        
        check_expected_regs()

        # FPSR and FPCR are still described as real registers, so they are
        # sent as normal writes.
        # This is the value 0xaaaaaaaa but only the bits that we can actually
        # set in reality.
        fpcontrol = 0xa800008a

        # First FPSR on its own.
        self.runCmd(f'register write fpsr 0x{fpcontrol:08x}')
        expected_registers['fpsr'] = HexValue(fpcontrol, repr_size=4)

        self.write_expected_reg_data(expected_registers)
        self.expect("next", substrs=["stop reason = step over"])

        check_expected_regs()

        # Then FPCR. This value is 0xaaaaaaaa reduced to the bits we can actually
        # set.
        fpcontrol = 0x02aaaa02
        self.runCmd(f'register write fpcr 0x{fpcontrol:08x}')
        expected_registers['fpcr'] = HexValue(fpcontrol, repr_size=4)

        self.write_expected_reg_data(expected_registers)
        self.expect("next", substrs=["stop reason = step over"])

        check_expected_regs()

        # We are faking SVE registers while outside of streaming mode, and
        # predicate registers and ffr have no real register to overlay.
        # We chose to make this an error instead of eating the write silently.

        value = ByteVector([0x98]*(svl_b // 8))
        self.expect(f'register write p0 "{value}"', error=True)
        check_expected_regs()
        self.expect(f'register write ffr "{value}"', error=True)
        check_expected_regs()

        # In theory we could test writing to ZA and ZT0, however this would
        # enable streaming mode. In streaming mode, their handling is the same
        # as on an SVE+SME system, and so is covered in other tests.

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
#        self.setup_test(Mode.SIMD, ZA.OFF)
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
#        self.setup_test(Mode.SSVE, ZA.ON)
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