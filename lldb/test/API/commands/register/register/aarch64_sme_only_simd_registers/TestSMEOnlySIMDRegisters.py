"""
Check reading and writing of SIMD registers on a system that only has SME. This
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
        cflags = "-march=armv8-a+sve"
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

    def expected_registers_simd(self):
        # TODO: proper vlen here
        register_values = []

        # V regs are {N <7 0s> N <7 0s>}
        v_regs = [f"v{n}" for n in range(32)]
        v_values = ["{" + " ".join(([f"0x{n:02x}"] + ["0x00"]*7) * 2) + "}" for n in range(1, 32)]
        register_values += list(zip(v_regs, v_values))

        register_values += [("fpsr", "0x50000015"),
                            ("fpcr", "0x05551505")]

        # Z regs are {N <7 0s> N <7 0s> <16 more 0s}
        z_regs = [f"z{n}" for n in range(32)]
        z_values = ["{" + " ".join((([f"0x{n:02x}"] + ["0x00"]*7) * 2) + ["0x00"] * 16) + "}" for n in range(1, 32)]
        register_values += list(zip(z_regs, z_values))

        # P regs are {<4 0s>}
        p_regs = [f"p{n}" for n in range(16)]
        p_values = ["{" + " ".join(["0x00"]*4) + "}" for n in range(0, 16)]
        register_values += list(zip(p_regs, p_values))

        # ffr is all 0s.
        register_values += [("ffr", "{0x00 0x00 0x00 0x00}")]

        return dict(register_values)

    def expected_registers_streaming(self):
        # TODO: proper vlen here
        register_values = []

        # Streaming SVE registers have their elements set to their number plus 1.
        # So z0 has elements of 0x01, z1 is 0x02 and so on.

        v_regs = [f"v{n}" for n in range(32)]
        v_values = ["{" + " ".join([f"0x{n:02x}"]*16) + "}" for n in range(1, 32)]
        register_values += list(zip(v_regs, v_values))

        register_values += [("fpsr", "0x50000015"),
                            ("fpcr", "0x05551505")]

        z_regs = [f"z{n}" for n in range(32)]
        z_values = ["{" + " ".join([f"0x{n:02x}"]*32) + "}" for n in range(1, 32)]
        register_values += list(zip(z_regs, z_values))

        # P registers have all emlements set to the same value and that value
        # cycles between 0xff, 0x55, 0x11, 0x01 and 0x00.
        p_regs = [f"p{n}" for n in range(16)]
        values = cycle([0xff, 0x55, 0x11, 0x01, 0x00]) 
        p_values = []
        for i in range(16):
            value = next(values)
            p_values.append("{" + " ".join([f'0x{value:02x}'] * 4) + "}")

        register_values += list(zip(p_regs, p_values))

        # ffr is all 0s.
        register_values += [("ffr", "{0x00 0x00 0x00 0x00}")]

        return dict(register_values)

    def sve_simd_registers_impl(self, mode):
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

        if mode == Mode.SSVE:
            # Writes to SVE should change SIMD and vice versa. Writes will be done
            # via. the streaming SVE register set.
            # TODO: pass actual vlen around here

            expected_registers = self.expected_registers_streaming()
            def check_expected_regs():
                self.expect(f'register read {" ".join(expected_registers.keys())}',
                        substrs=[f"{n} = {v}" for n, v in expected_registers.items()])

            check_expected_regs()

            # Write via Z0
            z_value = self.byte_vector([0x12]*32)
            self.runCmd(f'register write z0 "{z_value}"')

            # z0 and z0 should change but nothing else.
            expected_registers['z0'] = z_value
            expected_registers['v0'] = self.byte_vector([0x12]*16) 

            check_expected_regs()

            # We can do the same via a V register, the value will be extended and sent as
            # a Z write.
            v_value = self.byte_vector([0x34]*16)
            self.runCmd(f'register write v1 "{v_value}"')

            # The lower half of z1 is the v value, the upper part is the 0x2 that was previously in there.
            expected_registers['z1'] = self.byte_vector([0x34]*16 + [0x02]*16)
            expected_registers['v1'] = v_value 

            check_expected_regs()

            # Even though you can't set all these bits in reality, until we do
            # a step, it'll seem like we did.
            fpcontrol = "0xaaaaaaaa"

            self.runCmd(f'register write fpsr {fpcontrol}')
            expected_registers['fpsr'] = fpcontrol

            check_expected_regs()

            self.runCmd(f'register write fpcr {fpcontrol}')
            expected_registers['fpcr'] = fpcontrol

            check_expected_regs()

            p_value = self.byte_vector([0x12, 0x34, 0x56, 0x78])
            self.expect(f'register write p0 "{p_value}"')
            expected_registers['p0'] = p_value

            check_expected_regs()

            ffr_value = self.byte_vector([0x78, 0x56, 0x34, 0x12])
            self.expect(f'register write ffr "{ffr_value}"')
            expected_registers['ffr'] = ffr_value
            
            check_expected_regs()
        else:
            expected_registers = self.expected_registers_simd()
            def check_expected_regs():
                self.expect(f'register read {" ".join(expected_registers.keys())}',
                        substrs=[f"{n} = {v}" for n, v in expected_registers.items()])

            check_expected_regs()

            # In SIMD mode if you write Z0, only the parts that overlap V0 will
            # change.
            z_value = self.byte_vector([0x12]*32)
            self.runCmd(f'register write z0 "{z_value}"')

            # z0 and z0 should change but nothing else. We check the rest because
            # we are faking Z register data in this mode, and any offset mistake
            # could lead to modifying other registers.
            expected_registers['z0'] = self.byte_vector([0x12]*16 + [0x00]*16)
            expected_registers['v0'] = self.byte_vector([0x12]*16)

            check_expected_regs()

            # We can do the same via a V register, the value will be extended and sent as
            # a Z write.
            v_value = self.byte_vector([0x34]*16)
            self.runCmd(f'register write v1 "{v_value}"')

            expected_registers['z1'] = self.byte_vector([0x34]*16 + [0x00]*16)
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

            value = self.byte_vector([0x12, 0x34, 0x56, 0x78])
            self.expect(f'register write p0 "{value}"', error=True)
            check_expected_regs()
            self.expect(f'register write ffr "{value}"', error=True)
            check_expected_regs()

    @no_debug_info_test
    @skipIf(archs=no_match(["aarch64"]))
    @skipIf(oslist=no_match(["linux"]))
    def test_simd_registers_ssve(self):
        self.sve_simd_registers_impl(Mode.SSVE)

    @no_debug_info_test
    @skipIf(archs=no_match(["aarch64"]))
    @skipIf(oslist=no_match(["linux"]))
    def test_simd_registers_simd(self):
        self.sve_simd_registers_impl(Mode.SIMD)
