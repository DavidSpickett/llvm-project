//===-- RegisterTypeDetector_arm64.cpp -----------------------------------===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//

#include "RegisterTypeDetector_arm64.h"
#include "lldb/Target/RegisterTypeFlags.h"
#include "lldb/Target/RegisterTypeUnion.h"
#include "lldb/lldb-private-types.h"

// This file is built on all systems because it is used by native processes and
// core files, so we manually define the needed HWCAP values here.
// These values are the same for Linux and FreeBSD.

#define HWCAP_FPHP (1ULL << 9)
#define HWCAP_ASIMDHP (1ULL << 10)
#define HWCAP_DIT (1ULL << 24)
#define HWCAP_SSBS (1ULL << 28)

#define HWCAP2_BTI (1ULL << 17)
#define HWCAP2_MTE (1ULL << 18)
#define HWCAP2_AFP (1ULL << 20)
#define HWCAP2_SME (1ULL << 23)
#define HWCAP2_EBF16 (1ULL << 32)

using namespace lldb_private;

const RegisterType *Arm64RegisterTypeDetector::DetectSVCRType(uint64_t hwcap,
                                                              uint64_t hwcap2) {
  (void)hwcap;

  if (!(hwcap2 & HWCAP2_SME))
    return nullptr;

  // Represents the pseudo register that lldb-server builds, which itself
  // matches the architectural register SCVR. The fields match SVCR in the Arm
  // manual.
  static const RegisterTypeFlags svcr_flags("svcr_flags", 8,
                                            {{"ZA", 1}, {"SM", 0}});

  return &svcr_flags;
}

const RegisterType *
Arm64RegisterTypeDetector::DetectMTECtrlType(uint64_t hwcap, uint64_t hwcap2) {
  (void)hwcap;

  if (!(hwcap2 & HWCAP2_MTE))
    return nullptr;

  // Represents the contents of NT_ARM_TAGGED_ADDR_CTRL and the value passed
  // to prctl(PR_TAGGED_ADDR_CTRL...). Fields are derived from the defines
  // used to build the value.
  static const RegisterTypeEnum tcf_enum(
      "tcf_enum",
      {{0, "TCF_NONE"}, {1, "TCF_SYNC"}, {2, "TCF_ASYNC"}, {3, "TCF_ASYMM"}});
  static const RegisterTypeFlags mte_ctrl_flags(
      "mte_ctrl_flags", 8,
      {{"TAGS", 3, 18}, // 16 bit bitfield shifted up by PR_MTE_TAG_SHIFT.
       {"TCF", 1, 2, &tcf_enum},
       {"TAGGED_ADDR_ENABLE", 0}});

  return &mte_ctrl_flags;
}

const RegisterType *Arm64RegisterTypeDetector::DetectFPCRType(uint64_t hwcap,
                                                              uint64_t hwcap2) {
  static const RegisterTypeEnum rmode_enum(
      "rmode_enum", {{0, "RN"}, {1, "RP"}, {2, "RM"}, {3, "RZ"}});
  static RegisterTypeFlags fpcr_flags("fpcr_flags", 4, {});

  std::vector<RegisterTypeFlags::Field> fpcr_fields{
      {"AHP", 26}, {"DN", 25}, {"FZ", 24}, {"RMode", 22, 23, &rmode_enum},
      // Bits 21-20 are "Stride" which is unused in AArch64 state.
  };

  // FEAT_FP16 is indicated by the presence of FPHP (floating point half
  // precision) and ASIMDHP (Advanced SIMD half precision) features.
  if ((hwcap & HWCAP_FPHP) && (hwcap & HWCAP_ASIMDHP))
    fpcr_fields.push_back({"FZ16", 19});

  // Bits 18-16 are "Len" which is unused in AArch64 state.

  fpcr_fields.push_back({"IDE", 15});

  // Bit 14 is unused.
  if (hwcap2 & HWCAP2_EBF16)
    fpcr_fields.push_back({"EBF", 13});

  fpcr_fields.push_back({"IXE", 12});
  fpcr_fields.push_back({"UFE", 11});
  fpcr_fields.push_back({"OFE", 10});
  fpcr_fields.push_back({"DZE", 9});
  fpcr_fields.push_back({"IOE", 8});
  // Bits 7-3 reserved.

  if (hwcap2 & HWCAP2_AFP) {
    fpcr_fields.push_back({"NEP", 2});
    fpcr_fields.push_back({"AH", 1});
    fpcr_fields.push_back({"FIZ", 0});
  }

  fpcr_flags.SetFields(fpcr_fields);

  return &fpcr_flags;
}

const RegisterType *Arm64RegisterTypeDetector::DetectFPSRType(uint64_t hwcap,
                                                              uint64_t hwcap2) {
  // fpsr's contents are constant.
  (void)hwcap;
  (void)hwcap2;

  static const RegisterTypeFlags fpsr_flags(
      "fpsr_flags", 4,
      {
          // Bits 31-28 are N/Z/C/V, only used by AArch32.
          {"QC", 27},
          // Bits 26-8 reserved.
          {"IDC", 7},
          // Bits 6-5 reserved.
          {"IXC", 4},
          {"UFC", 3},
          {"OFC", 2},
          {"DZC", 1},
          {"IOC", 0},
      });

  return &fpsr_flags;
}

const RegisterType *Arm64RegisterTypeDetector::DetectCPSRType(uint64_t hwcap,
                                                              uint64_t hwcap2) {
  // The fields here are a combination of the Arm manual's SPSR_EL1,
  // plus a few changes where Linux has decided not to make use of them at all,
  // or at least not from userspace.
  static RegisterTypeFlags cpsr_flags("cpsr_flags", 4, {});

  // Status bits that are always present.
  std::vector<RegisterTypeFlags::Field> cpsr_fields{
      {"N", 31}, {"Z", 30}, {"C", 29}, {"V", 28},
      // Bits 27-26 reserved.
  };

  if (hwcap2 & HWCAP2_MTE)
    cpsr_fields.push_back({"TCO", 25});
  if (hwcap & HWCAP_DIT)
    cpsr_fields.push_back({"DIT", 24});

  // UAO and PAN are bits 23 and 22 and have no meaning for userspace so
  // are treated as reserved by the kernels.

  cpsr_fields.push_back({"SS", 21});
  cpsr_fields.push_back({"IL", 20});
  // Bits 19-14 reserved.

  // Bit 13, ALLINT, requires FEAT_NMI that isn't relevant to userspace, and we
  // can't detect either, don't show this field.
  if (hwcap & HWCAP_SSBS)
    cpsr_fields.push_back({"SSBS", 12});
  if (hwcap2 & HWCAP2_BTI)
    cpsr_fields.push_back({"BTYPE", 10, 11});

  cpsr_fields.push_back({"D", 9});
  cpsr_fields.push_back({"A", 8});
  cpsr_fields.push_back({"I", 7});
  cpsr_fields.push_back({"F", 6});
  // Bit 5 reserved
  // Called "M" in the ARMARM.
  cpsr_fields.push_back({"nRW", 4});
  // This is a 4 bit field M[3:0] in the ARMARM, we split it into parts.
  cpsr_fields.push_back({"EL", 2, 3});
  // Bit 1 is unused and expected to be 0.
  cpsr_fields.push_back({"SP", 0});

  cpsr_flags.SetFields(cpsr_fields);

  static RegisterTypeFlags cpsr_flags_reversed("cpsr_raw_bits", 4, {});
  const static std::vector<RegisterTypeFlags::Field> raw_bits{
      {"31", 31}, {"30", 30}, {"29", 29}, {"28", 28}, {"27", 27}, {"26", 26},
      {"25", 25}, {"24", 24}, {"23", 23}, {"22", 22}, {"21", 21}, {"20", 20},
      {"19", 19}, {"18", 18}, {"17", 17}, {"16", 16}, {"15", 15}, {"14", 14},
      {"13", 13}, {"12", 12}, {"11", 11}, {"10", 10}, {"9", 9},   {"8", 8},
      {"7", 7},   {"6", 6},   {"5", 5},   {"4", 4},   {"3", 3},   {"2", 2},
      {"1", 1},   {"0", 0},
  };

  cpsr_flags_reversed.SetFields(raw_bits);

  static RegisterTypeUnion cpsr_union(
      "cpsr_union",
      {{"normal", &cpsr_flags}, {"raw_bits", &cpsr_flags_reversed}});

  return &cpsr_union;
}

void Arm64RegisterTypeDetector::DetectTypes(uint64_t hwcap, uint64_t hwcap2) {
  for (auto &reg : m_registers)
    reg.m_type = reg.m_detector(hwcap, hwcap2);
  m_has_detected = true;
}

void Arm64RegisterTypeDetector::UpdateRegisterInfo(const RegisterInfo *reg_info,
                                                   uint32_t num_regs) {
  assert(m_has_detected &&
         "Must call DetectTypes before updating register info.");

  // Register names will not be duplicated, so we do not want to compare against
  // one if it has already been found. Each time we find one, we erase it from
  // this list.
  std::vector<std::pair<llvm::StringRef, const RegisterType *>>
      search_registers;
  for (const auto &reg : m_registers) {
    // It is possible that a register is all extension dependent fields, and
    // none of them are present.
    if (reg.m_type)
      search_registers.push_back({reg.m_name, reg.m_type});
  }

  // Walk register information while there are registers we know need
  // to be updated. Example:
  // Register information: [a, b, c, d]
  // To be patched: [b, c]
  // * a != b, a != c, do nothing and move on.
  // * b == b, patch b, new patch list is [c], move on.
  // * c == c, patch c, patch list is empty, exit early without looking at d.
  for (uint32_t idx = 0; idx < num_regs && search_registers.size();
       ++idx, ++reg_info) {
    auto reg_it = std::find_if(
        search_registers.cbegin(), search_registers.cend(),
        [reg_info](auto reg) { return reg.first == reg_info->name; });

    if (reg_it != search_registers.end()) {
      // Attach the field information.
      reg_info->register_type = reg_it->second;
      // We do not expect to see this name again so don't look for it again.
      search_registers.erase(reg_it);
    }
  }

  // We do not assert that search_registers is empty here, because it may
  // contain registers from optional extensions that are not present on the
  // current target.
}
