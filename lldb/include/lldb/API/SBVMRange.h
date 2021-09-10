//===-- SBVMRange.h ---------------------------------------------*- C++ -*-===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//

#ifndef LLDB_API_SBVMRANGE_H
#define LLDB_API_SBVMRANGE_H

#include "lldb/API/SBDefines.h"

namespace lldb {

class LLDB_API SBVMRange {
public:
  // TODO: what constructors do I actually need?
  SBVMRange();

  SBVMRange(const lldb::SBVMRange &rhs);

  SBVMRange(const lldb::VMRangeSP &vmrange_sp);

  ~SBVMRange();

  const lldb::SBVMRange &operator=(const lldb::SBVMRange &rhs);
  operator bool() const;

  bool IsValid() const;

  lldb::SBAddress GetBaseAddress() const;

  lldb::SBAddress GetEndAddress() const;

  void SetBaseAddress(const lldb::SBAddress &addr);

  void SetEndAddress(const lldb::SBAddress &addr);

  bool GetDescription(lldb::SBStream &description);

private:
  friend class SBProcess;

  lldb_private::VMRange &ref();

  const lldb_private::VMRange &ref() const;

  std::shared_ptr<lldb_private::VMRange> m_opaque_sp;
};

} // namespace lldb

#endif // LLDB_API_SBVMRANGE_H
