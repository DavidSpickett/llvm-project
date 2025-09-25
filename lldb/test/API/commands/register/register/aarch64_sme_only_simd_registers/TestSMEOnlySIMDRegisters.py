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

    def byte_vector(self, elements):
        return "{" + " ".join([f'0x{b:02x}' for b in elements]) + "}"

    def reg_names(self, prefix, count):
        return [f'{prefix}{n}' for n in range(count)]

    def expected_fpr_control(self):
        return [("fpsr", "0x50000015"), ("fpcr", "0x05551505")]

    def expected_registers_simd(self, svl_b):
        register_values = []

        # V regs are {N <7 0s> N <7 0s>} because we set the bottom element to N
        # where N is 1 + the register index.
        v_values = [self.byte_vector([n+1] + [0] * 7 + [n+1] + [0] * 7) for n in range(32)]
        register_values += list(zip(self.reg_names('v', 32), v_values, strict=True))

        register_values += self.expected_fpr_control()

        # Z regs are {N <7 0s> N <7 0s> <16 more 0s}. First half overlaps a V
        # register, the second half we fake 0s for as there is no real Z register
        # in non-streaming mode.
        z_values = [self.byte_vector([n+1] + [0] * 7 + [n+1] + [0] * 7 + [0] * (svl_b - 16)) for n in range(32)]
        register_values += list(zip(self.reg_names('z', 32), z_values, strict=True))

        # P regs are {<4 0s>}, we fake the value.
        p_values = [self.byte_vector([0]*(svl_b // 8)) for _ in range(16)]
        register_values += list(zip(self.reg_names('p', 16), p_values, strict=True))

        # ffr is all 0s, again a fake value.
        register_values += [("ffr", self.byte_vector([0]*(svl_b // 8)))]

        register_values += [
            # SVCR shows that ZA and streaming mode are off.
            ('svcr', '0x0000000000000000'),
            # SVG is the streaming vector length in granules.
            ('svg', f'0x{svl_b // 8:016x}'),
        ]

        # ZA is being faked so is all 0s it is a square with svl_b sides.
        register_values += [('za', self.byte_vector([0x0]*(svl_b*svl_b)))]

        # TODO: don't check this if we don't have SME2
        # Fake zt0.
        register_values += [('zt0', self.byte_vector([0x00]*(svl_b*2)))]

        return dict(register_values)

    def expected_registers_streaming(self, svl_b):
        register_values = []

        # Streaming SVE registers have their elements set to their number plus 1.
        # So z0 has elements of 0x01, z1 is 0x02 and so on.
        v_values = [self.byte_vector([n+1]*16) for n in range(32)]
        register_values += list(zip(self.reg_names('v', 32), v_values, strict=True))

        register_values += self.expected_fpr_control() 

        z_values = [self.byte_vector([n+1]*svl_b) for n in range(32)]
        register_values += list(zip(self.reg_names('z', 32), z_values, strict=True))

        # P registers have all emlements set to the same value and that value
        # cycles between 0xff, 0x55, 0x11, 0x01 and 0x00.
        p_values = []
        for i, v in zip(range(16), cycle([0xff, 0x55, 0x11, 0x01, 0x00])):
            p_values.append(self.byte_vector([v]*(svl_b // 8)))

        register_values += list(zip(self.reg_names('p', 16), p_values, strict=True))

        # ffr is all 0s.
        register_values += [("ffr", self.byte_vector([0]*(svl_b // 8)))]

        register_values += [
            # Streaming mode and ZA are on.
            ('svcr', '0x0000000000000003'),
            # SVG is the streaming vector length in granules.
            ('svg', f'0x{svl_b // 8:016x}'),
        ]

        register_values += [('za', self.byte_vector(list(range(1, svl_b+1)) * svl_b))]

        # TODO: don't check this if we don't have SME2
        register_values += [('zt0', self.byte_vector(list(range(1, (svl_b*2)+1))))]

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
#        z_value = self.byte_vector([0x12]*svl_b)
#        self.runCmd(f'register write z0 "{z_value}"')
#
#        # z0 and v0 should change but nothing else.
#        expected_registers['z0'] = z_value
#        expected_registers['v0'] = self.byte_vector([0x12]*16) 
#
#        check_expected_regs()
#
#        # We can do the same via a V register, the value will be extended and sent as
#        # a Z write.
#        v_value = self.byte_vector([0x34]*16)
#        self.runCmd(f'register write v1 "{v_value}"')
#
#        # The lower half of z1 is the v value, the upper part is the 0x2 that was previously in there.
#        expected_registers['z1'] = self.byte_vector([0x34]*16 + [0x02]*(svl_b - 16))
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
#        p_value = self.byte_vector([0x65] * (svl_b // 8))
#        self.expect(f'register write p0 "{p_value}"')
#        expected_registers['p0'] = p_value
#
#        check_expected_regs()
#
#        ffr_value = self.byte_vector([0x78] * (svl_b // 8))
#        self.expect(f'register write ffr "{ffr_value}"')
#        expected_registers['ffr'] = ffr_value
#        
#        check_expected_regs()
#
#        za_value = self.byte_vector(list(range(2, svl_b+2)) * svl_b)
#        self.expect(f'register write za "{za_value}"')
#        expected_registers['za'] = za_value
#
#        check_expected_regs()
#
#        # TODO: only do this for SME2
#        zt0_value = self.byte_vector(list(range(2, (svl_b*2)+2)))
#        self.expect(f'register write zt0 "{zt0_value}"')
#        expected_registers['zt0'] = zt0_value
#
#        check_expected_regs()
#
#    @no_debug_info_test
#    @skipIf(archs=no_match(["aarch64"]))
#    @skipIf(oslist=no_match(["linux"]))
#    def test_simd_registers_simd(self):
#        self.setup_test(Mode.SIMD)
#        svl_b = self.get_svl_b()
#
#        expected_registers = self.expected_registers_simd(svl_b)
#        check_expected_regs = self.check_expected_regs_fn(expected_registers)
#
#        check_expected_regs()
#
#        # In SIMD mode if you write Z0, only the parts that overlap V0 will
#        # change.
#        z_value = self.byte_vector([0x12]*svl_b)
#        self.runCmd(f'register write z0 "{z_value}"')
#
#        # z0 and z0 should change but nothing else. We check the rest because
#        # we are faking Z register data in this mode, and any offset mistake
#        # could lead to modifying other registers.
#        expected_registers['z0'] = self.byte_vector([0x12]*16 + [0x00]*(svl_b - 16))
#        expected_registers['v0'] = self.byte_vector([0x12]*16)
#
#        check_expected_regs()
#
#        # We can do the same via a V register, the value will be extended and sent as
#        # a Z write.
#        v_value = self.byte_vector([0x34]*16)
#        self.runCmd(f'register write v1 "{v_value}"')
#
#        expected_registers['z1'] = self.byte_vector([0x34]*16 + [0x00]*(svl_b - 16))
#        expected_registers['v1'] = v_value
#
#        check_expected_regs()
#
#        # FPSR and FPCR are still described as real registers, so they are
#        # sent as normal writes.
#        # Even though you can't set all these bits in reality, until we do
#        # a step, it'll seem like we did.
#        fpcontrol = "0xaaaaaaaa"
#
#        # First FPSR on its own.
#        self.runCmd(f'register write fpsr {fpcontrol}')
#        expected_registers['fpsr'] = fpcontrol
#
#        check_expected_regs()
#
#        # Then FPCR.
#        self.runCmd(f'register write fpcr {fpcontrol}')
#        expected_registers['fpcr'] = fpcontrol
#
#        check_expected_regs()
#
#        # We are faking SVE registers while outside of streaming mode, and
#        # predicate registers and ffr have no real register to overlay.
#        # We chose to make this an error instead of eating the write silently.
#
#        value = self.byte_vector([0x98]*(svl_b // 8))
#        self.expect(f'register write p0 "{value}"', error=True)
#        check_expected_regs()
#        self.expect(f'register write ffr "{value}"', error=True)
#        check_expected_regs()
#
#        # Writing ZA or ZT0 would take us into streaming mode. This transition
#        # is tested in the SVE+SME tests.

    @no_debug_info_test
    @skipIf(archs=no_match(["aarch64"]))
    @skipIf(oslist=no_match(["linux"]))
    def test_expr_simd_to_streaming(self):
        # TODO: this test requires that you have streaming mode too!!!
        self.setup_test(Mode.SIMD)
        svl_b = self.get_svl_b()
 
        expected_registers = self.expected_registers_simd(svl_b)
        check_expected_regs = self.check_expected_regs_fn(expected_registers)
 
        check_expected_regs()
        self.expect("expression expr_enter_streaming_mode()")
        check_expected_regs()

    # TODO: check streaming to streaming expression, and non-streaming to non-streaming.