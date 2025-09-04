"""
Check reading and writing of SIMD registers on a system that only has SME. This
means that the "SVE" registers are only active during streaming mode.
"""

from enum import Enum
import lldb
from lldbsuite.test.decorators import *
from lldbsuite.test.lldbtest import *
from lldbsuite.test import lldbutil


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

    def make_simd_value(self, n):
        pad = " ".join(["0x00"] * 7)
        return "{{0x{:02x} {} 0x{:02x} {}}}".format(n, pad, n, pad)

    def make_sve_value(self, n):
        # TODO: find actual vlen
        return "{" + " ".join([f"0x{n:02x}" for _ in range(32)]) + "}"

    def check_sve_values(self):
        for i in range(32):
            self.expect(f"register read z{i}", substrs=[self.make_sve_value(i + 1)])

    def check_simd_values(self, value_offset):
        # These are 128 bit registers, so getting them from the API as unsigned
        # values doesn't work. Check the command output instead.
        for i in range(32):
            self.expect(
                "register read v{}".format(i),
                substrs=[self.make_simd_value(i + value_offset)],
            )

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
            self.check_sve_values()
        else:
            self.check_simd_values(1)
        # self.runCmd("expression write_simd_regs(1)")
        # self.check_simd_values(0)

        # # Write a new set of values. The kernel will move the program back to
        # # non-streaming mode here.
        # for i in range(32):
        #     self.runCmd(
        #         'register write v{} "{}"'.format(i, self.make_simd_value(i + 1))
        #     )

        # # Should be visible within lldb.
        # self.check_simd_values(1)

        # # The program should agree with lldb.
        # self.expect("continue", substrs=["exited with status = 0"])

    @no_debug_info_test
    @skipIf(archs=no_match(["aarch64"]))
    @skipIf(oslist=no_match(["linux"]))
    def test_simd_registers_ssve(self):
        """Test read/write of SIMD registers when in SSVE mode."""
        self.sve_simd_registers_impl(Mode.SSVE)
