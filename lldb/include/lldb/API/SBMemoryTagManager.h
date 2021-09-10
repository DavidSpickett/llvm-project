//===-- SBMemoryTagManager.h ------------------------------------*- C++ -*-===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//

#ifndef LLDB_API_SBMEMORYTAGMANAGER_H
#define LLDB_API_SBMEMORYTAGMANAGER_H

#include "lldb/API/SBDefines.h"
#include "lldb/API/SBError.h"
#include "lldb/API/SBMemoryRegionInfoList.h"
#include "lldb/API/SBStream.h"
#include "lldb/API/SBVMRange.h"
#include "lldb/API/SBVMRangeList.h"
#include "lldb/Target/MemoryTagManager.h"

namespace lldb {

class LLDB_API SBMemoryTagManager {
public:
  // TODO: what constructors do I actually need?
  SBMemoryTagManager();

  SBMemoryTagManager(const lldb::SBMemoryTagManager &rhs);

  ~SBMemoryTagManager();

  const lldb::SBMemoryTagManager &
  operator=(const lldb::SBMemoryTagManager &rhs);
  operator bool() const;

  bool IsValid() const;

  bool GetDescription(lldb::SBStream &description);

  const char *GetTagTypeName() const;

  int GetAllocationTagType() const;

  addr_t GetGranuleSize() const;

  lldb::SBError MakeTaggedRange(int32_t type, const lldb::SBVMRange &range,
                                const lldb::SBMemoryRegionInfoList &regions,
                                lldb::SBVMRange &result) const;

  lldb::SBError MakeTaggedRanges(int32_t type, const lldb::SBVMRange &range,
                                 const lldb::SBMemoryRegionInfoList &regions,
                                 lldb::SBVMRangeList &result) const;

private:
  friend class SBProcess;
  friend class SBMemoryTagManagerList;

  const lldb_private::MemoryTagManager *GetPtr() const;

  void SetPtr(const lldb_private::MemoryTagManager *tag_manager_ptr);

  SBMemoryTagManager(const lldb_private::MemoryTagManager *tag_manager_ptr);

  const lldb_private::MemoryTagManager *m_opaque_ptr = nullptr;
};

} // namespace lldb

#endif // LLDB_API_SBMEMORYTAGMANAGER_H
