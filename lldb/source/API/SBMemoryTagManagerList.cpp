//===-- SBMemoryTagManagerList.cpp ----------------------------------------===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//

#include "lldb/API/SBMemoryTagManagerList.h"
#include "lldb/API/SBMemoryTagManager.h"
#include "lldb/API/SBStream.h"
#include "lldb/Target/MemoryTagManager.h"

#include <vector>

using namespace lldb;
using namespace lldb_private;

class MemoryTagManagerListImpl {
public:
  MemoryTagManagerListImpl() : m_tag_managers() {}

  MemoryTagManagerListImpl(const MemoryTagManagerListImpl &rhs)
      : m_tag_managers(rhs.m_tag_managers) {}

  MemoryTagManagerListImpl &operator=(const MemoryTagManagerListImpl &rhs) {
    if (this == &rhs)
      return *this;
    m_tag_managers = rhs.m_tag_managers;
    return *this;
  }

  size_t GetSize() const { return m_tag_managers.size(); }

  void Reserve(size_t capacity) { return m_tag_managers.reserve(capacity); }

  void Append(const lldb_private::MemoryTagManager *tag_manager) {
    m_tag_managers.push_back(tag_manager);
  }

  void Append(const MemoryTagManagerListImpl &list) {
    Reserve(GetSize() + list.GetSize());

    for (const auto &val : list.m_tag_managers)
      Append(val);
  }

  void Clear() { m_tag_managers.clear(); }

  bool GetMemoryTagManagerAtIndex(
      size_t index,
      // TODO: ref to ptr is strange?
      const lldb_private::MemoryTagManager *&tag_manager) {
    if (index >= GetSize())
      return false;
    tag_manager = m_tag_managers[index];
    return true;
  }

  std::vector<const lldb_private::MemoryTagManager *> &Ref() {
    return m_tag_managers;
  }

  const std::vector<const lldb_private::MemoryTagManager *> &Ref() const {
    return m_tag_managers;
  }

private:
  std::vector<const lldb_private::MemoryTagManager *> m_tag_managers;
};

std::vector<const lldb_private::MemoryTagManager *> &
SBMemoryTagManagerList::ref() {
  return m_opaque_up->Ref();
}

const std::vector<const lldb_private::MemoryTagManager *> &
SBMemoryTagManagerList::ref() const {
  return m_opaque_up->Ref();
}

SBMemoryTagManagerList::SBMemoryTagManagerList()
    : m_opaque_up(new MemoryTagManagerListImpl()) {}

SBMemoryTagManagerList::SBMemoryTagManagerList(
    const SBMemoryTagManagerList &rhs)
    : m_opaque_up(new MemoryTagManagerListImpl(*rhs.m_opaque_up)) {}

SBMemoryTagManagerList::~SBMemoryTagManagerList() = default;

const SBMemoryTagManagerList &
SBMemoryTagManagerList::operator=(const SBMemoryTagManagerList &rhs) {
  if (this != &rhs) {
    *m_opaque_up = *rhs.m_opaque_up;
  }
  return *this;
}

uint32_t SBMemoryTagManagerList::GetSize() const {
  return m_opaque_up->GetSize();
}

bool SBMemoryTagManagerList::GetMemoryTagManagerAtIndex(
    uint32_t idx, SBMemoryTagManager &tag_manager) {
  const lldb_private::MemoryTagManager *tag_manager_ptr = nullptr;
  bool success = m_opaque_up->GetMemoryTagManagerAtIndex(idx, tag_manager_ptr);

  if (success)
    tag_manager.SetPtr(tag_manager_ptr);

  return success;
}

void SBMemoryTagManagerList::Clear() { m_opaque_up->Clear(); }

void SBMemoryTagManagerList::Append(SBMemoryTagManager &sb_tag_manager) {
  m_opaque_up->Append(sb_tag_manager.GetPtr());
}

void SBMemoryTagManagerList::Append(
    SBMemoryTagManagerList &sb_tag_manager_list) {
  m_opaque_up->Append(*sb_tag_manager_list);
}

const MemoryTagManagerListImpl *SBMemoryTagManagerList::operator->() const {
  return m_opaque_up.get();
}

const MemoryTagManagerListImpl &SBMemoryTagManagerList::operator*() const {
  assert(m_opaque_up.get());
  return *m_opaque_up;
}
