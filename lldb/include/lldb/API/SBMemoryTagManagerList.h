//===-- SBMemoryTagManagerList.h --------------------------------*- C++ -*-===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//

#ifndef LLDB_API_SBMEMORYTAGMANAGERLIST_H
#define LLDB_API_SBMEMORYTAGMANAGERLIST_H

#include "lldb/API/SBDefines.h"
#include "lldb/API/SBMemoryTagManager.h"

class MemoryTagManagerListImpl;

namespace lldb {

class LLDB_API SBMemoryTagManagerList {
public:
  SBMemoryTagManagerList();

  SBMemoryTagManagerList(const lldb::SBMemoryTagManagerList &rhs);

  const SBMemoryTagManagerList &operator=(const SBMemoryTagManagerList &rhs);

  ~SBMemoryTagManagerList();

  uint32_t GetSize() const;

  bool GetMemoryTagManagerAtIndex(uint32_t idx,
                                  SBMemoryTagManager &tag_manager);

  void Append(lldb::SBMemoryTagManager &tag_manager);

  void Append(lldb::SBMemoryTagManagerList &tag_manager_list);

  void Clear();

protected:
  // TODO: needed?
  const MemoryTagManagerListImpl *operator->() const;

  const MemoryTagManagerListImpl &operator*() const;

private:
  std::vector<const lldb_private::MemoryTagManager *> &ref();

  const std::vector<const lldb_private::MemoryTagManager *> &ref() const;

  std::unique_ptr<MemoryTagManagerListImpl> m_opaque_up;
};

} // namespace lldb

#endif // LLDB_API_SBMEMORYTAGMANAGERLIST_H
