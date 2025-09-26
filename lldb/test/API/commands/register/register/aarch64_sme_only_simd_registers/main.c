#include <stdint.h>
#include <string.h>
#include <sys/prctl.h>

#ifndef PR_SME_GET_VL
#define PR_SME_GET_VL 64
#endif

// Doing a syscall exits streaming mode, but we need to use this during an
// expression in streaming mode. So it's set by main and we reference this
// later.
int svl_b = 0;

static void write_fp_control() {
  // Some of these bits won't get set, this is fine. Just needs to be recongisable
  // from inside the debugger.
  uint64_t val = 0x5555555555555555ULL;
  asm volatile ("msr fpcr, %0" :: "r"(val));
  asm volatile ("msr fpsr, %0" :: "r"(val));
}

static void write_sve_regs() {
  // We do not explicitly set ffr here because doing so requires the smefa64
  // extension. To have that extension you have to have SVE outside of streaming
  // mode which we do not have.

  asm volatile("ptrue p0.b\n\t");
  asm volatile("ptrue p1.h\n\t");
  asm volatile("ptrue p2.s\n\t");
  asm volatile("ptrue p3.d\n\t");
  asm volatile("pfalse p4.b\n\t");
  asm volatile("ptrue p5.b\n\t");
  asm volatile("ptrue p6.h\n\t");
  asm volatile("ptrue p7.s\n\t");
  asm volatile("ptrue p8.d\n\t");
  asm volatile("pfalse p9.b\n\t");
  asm volatile("ptrue p10.b\n\t");
  asm volatile("ptrue p11.h\n\t");
  asm volatile("ptrue p12.s\n\t");
  asm volatile("ptrue p13.d\n\t");
  asm volatile("pfalse p14.b\n\t");
  asm volatile("ptrue p15.b\n\t");

  asm volatile("cpy  z0.b, p0/z, #1\n\t");
  asm volatile("cpy  z1.b, p5/z, #2\n\t");
  asm volatile("cpy  z2.b, p10/z, #3\n\t");
  asm volatile("cpy  z3.b, p15/z, #4\n\t");
  asm volatile("cpy  z4.b, p0/z, #5\n\t");
  asm volatile("cpy  z5.b, p5/z, #6\n\t");
  asm volatile("cpy  z6.b, p10/z, #7\n\t");
  asm volatile("cpy  z7.b, p15/z, #8\n\t");
  asm volatile("cpy  z8.b, p0/z, #9\n\t");
  asm volatile("cpy  z9.b, p5/z, #10\n\t");
  asm volatile("cpy  z10.b, p10/z, #11\n\t");
  asm volatile("cpy  z11.b, p15/z, #12\n\t");
  asm volatile("cpy  z12.b, p0/z, #13\n\t");
  asm volatile("cpy  z13.b, p5/z, #14\n\t");
  asm volatile("cpy  z14.b, p10/z, #15\n\t");
  asm volatile("cpy  z15.b, p15/z, #16\n\t");
  asm volatile("cpy  z16.b, p0/z, #17\n\t");
  asm volatile("cpy  z17.b, p5/z, #18\n\t");
  asm volatile("cpy  z18.b, p10/z, #19\n\t");
  asm volatile("cpy  z19.b, p15/z, #20\n\t");
  asm volatile("cpy  z20.b, p0/z, #21\n\t");
  asm volatile("cpy  z21.b, p5/z, #22\n\t");
  asm volatile("cpy  z22.b, p10/z, #23\n\t");
  asm volatile("cpy  z23.b, p15/z, #24\n\t");
  asm volatile("cpy  z24.b, p0/z, #25\n\t");
  asm volatile("cpy  z25.b, p5/z, #26\n\t");
  asm volatile("cpy  z26.b, p10/z, #27\n\t");
  asm volatile("cpy  z27.b, p15/z, #28\n\t");
  asm volatile("cpy  z28.b, p0/z, #29\n\t");
  asm volatile("cpy  z29.b, p5/z, #30\n\t");
  asm volatile("cpy  z30.b, p10/z, #31\n\t");
  asm volatile("cpy  z31.b, p15/z, #32\n\t");
  
  write_fp_control();
}

static void write_sme_regs(int svl_b) {
  uint8_t value_offset = 1;

#define MAX_VL_BYTES 256
  uint8_t data[MAX_VL_BYTES];

  // ldr za will actually wrap the selected vector row, by the number of rows
  // you have. So setting one that didn't exist would actually set one that did.
  // That's why we need the streaming vector length here.
  for (int i = 0; i < svl_b; ++i) {
    // Glibc's memset uses instructions not allowed in streaming mode, so we
    // do this, and make sure it's not optimised into memset.
    for (unsigned j = 0; j < MAX_VL_BYTES; ++j)
      data[j] = j + value_offset;

    // Each one of these loads a VL sized row of ZA.
    asm volatile("mov w12, %w0\n\t"
                 "ldr za[w12, 0], [%1]\n\t" ::"r"(i),
                 "r"(&data)
                 : "w12");
  }
#undef MAX_VL_BYTES

  // TODO: detect this
  /*if (has_zt0)*/ {
#define ZTO_LEN (512 / 8)
    uint8_t data[ZTO_LEN];
    for (unsigned i = 0; i < ZTO_LEN; ++i)
      data[i] = i + value_offset;

    asm volatile("ldr zt0, [%0]" ::"r"(&data));
#undef ZT0_LEN
  }
}

static void write_simd_regs() {
  // base is added to each value. If base = 1, then v0 = 1, v1 = 2, etc.
  unsigned base = 1;

#define WRITE_SIMD(NUM)                                                        \
  asm volatile("MOV v" #NUM ".d[0], %0\n\t"                                    \
               "MOV v" #NUM ".d[1], %0\n\t" ::"r"((uint64_t)(base + NUM)))

  WRITE_SIMD(0);
  WRITE_SIMD(1);
  WRITE_SIMD(2);
  WRITE_SIMD(3);
  WRITE_SIMD(4);
  WRITE_SIMD(5);
  WRITE_SIMD(6);
  WRITE_SIMD(7);
  WRITE_SIMD(8);
  WRITE_SIMD(9);
  WRITE_SIMD(10);
  WRITE_SIMD(11);
  WRITE_SIMD(12);
  WRITE_SIMD(13);
  WRITE_SIMD(14);
  WRITE_SIMD(15);
  WRITE_SIMD(16);
  WRITE_SIMD(17);
  WRITE_SIMD(18);
  WRITE_SIMD(19);
  WRITE_SIMD(20);
  WRITE_SIMD(21);
  WRITE_SIMD(22);
  WRITE_SIMD(23);
  WRITE_SIMD(24);
  WRITE_SIMD(25);
  WRITE_SIMD(26);
  WRITE_SIMD(27);
  WRITE_SIMD(28);
  WRITE_SIMD(29);
  WRITE_SIMD(30);
  WRITE_SIMD(31);
  
  write_fp_control();
}

#define SM_INST(c) asm volatile("msr s0_3_c4_c" #c "_3, xzr")
#define SMSTART SM_INST(7)
#define SMSTART_SM SM_INST(3)
#define SMSTART_ZA SM_INST(5)
#define SMSTOP SM_INST(6)
#define SMSTOP_SM SM_INST(2)
#define SMSTOP_ZA SM_INST(4)

// TODO: test re-entering streaming mode with ZA enabled and disabled?

void expr_enter_streaming_mode() {
  SMSTART;
  write_sve_regs();
  write_sme_regs(svl_b);
}

void expr_exit_streaming_mode() {
  SMSTOP;
  write_simd_regs();
}

bool 

int main() {
#ifdef SSVE
  // Get SVL first because doing a syscall makes you exit streaming mode.
  svl_b = prctl(PR_SME_GET_VL); 
  SMSTART;
  write_sve_regs();
  write_sme_regs(svl_b);
#else
  write_simd_regs();
  // TODO: what about an active ZA outside of streaming mode?
#endif

  return 0; // Set a break point here.
}
