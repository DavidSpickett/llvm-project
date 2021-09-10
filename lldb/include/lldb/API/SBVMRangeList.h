//===-- SBVMRangeList.h -------------------------------------------*- C++
//-*-===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//

#ifndef LLDB_API_SBVMRANGELIST_H
#define LLDB_API_SBVMRANGELIST_H

#include "lldb/API/SBDefines.h"

class VMRangeListImpl;

namespace lldb {

class LLDB_API SBVMRangeList {
public:
  SBVMRangeList();

  SBVMRangeList(const lldb::SBVMRangeList &rhs);

  ~SBVMRangeList();

  explicit operator bool() const;

  bool IsValid() const;

  void Clear();

  void Append(const lldb::SBVMRange &range_obj);

  void Append(const lldb::SBVMRangeList &range_list);

  uint32_t GetSize() const;

  lldb::SBVMRange GetValueAtIndex(uint32_t idx) const;

  const lldb::SBVMRangeList &operator=(const lldb::SBVMRangeList &rhs);

protected:
  // only useful for visualizing the pointer or comparing two SBVMRangeLists to
  // see if they are backed by the same underlying Impl.
  void *opaque_ptr();

private:
  SBVMRangeList(const VMRangeListImpl *lldb_object_ptr);

  void Append(lldb::VMRangeSP &vmrange_sp);

  void CreateIfNeeded();

  VMRangeListImpl *operator->();

  VMRangeListImpl &operator*();

  const VMRangeListImpl *operator->() const;

  const VMRangeListImpl &operator*() const;

  VMRangeListImpl &ref();

  std::unique_ptr<VMRangeListImpl> m_opaque_up;
};

} // namespace lldb

#endif // LLDB_API_SBVMRANGELIST_H
