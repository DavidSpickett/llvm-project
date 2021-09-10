//===-- SBVMRangeList.cpp -------------------------------------------------===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//

#include "lldb/API/SBVMRangeList.h"
#include "lldb/API/SBStream.h"
#include "lldb/API/SBVMRange.h"

#include <vector>

using namespace lldb;
using namespace lldb_private;

// TODO: feels like you could generalise these ListImpls

class VMRangeListImpl {
public:
  VMRangeListImpl() : m_ranges() {}

  VMRangeListImpl(const VMRangeListImpl &rhs) : m_ranges(rhs.m_ranges) {}

  VMRangeListImpl &operator=(const VMRangeListImpl &rhs) {
    if (this == &rhs)
      return *this;
    m_ranges = rhs.m_ranges;
    return *this;
  }

  uint32_t GetSize() { return m_ranges.size(); }

  void Append(const lldb::SBVMRange &sb_vmrange) {
    m_ranges.push_back(sb_vmrange);
  }

  void Append(const VMRangeListImpl &list) {
    for (auto val : list.m_ranges)
      Append(val);
  }

  lldb::SBVMRange GetValueAtIndex(uint32_t index) {
    if (index >= GetSize())
      return lldb::SBVMRange();
    return m_ranges[index];
  }

private:
  std::vector<lldb::SBVMRange> m_ranges;
};

SBVMRangeList::SBVMRangeList() : m_opaque_up() {}

SBVMRangeList::SBVMRangeList(const SBVMRangeList &rhs) : m_opaque_up() {
  if (rhs.IsValid())
    m_opaque_up = std::make_unique<VMRangeListImpl>(*rhs);
}

SBVMRangeList::SBVMRangeList(const VMRangeListImpl *lldb_object_ptr)
    : m_opaque_up() {
  if (lldb_object_ptr)
    m_opaque_up = std::make_unique<VMRangeListImpl>(*lldb_object_ptr);
}

SBVMRangeList::~SBVMRangeList() = default;

bool SBVMRangeList::IsValid() const { return this->operator bool(); }
SBVMRangeList::operator bool() const { return (m_opaque_up != nullptr); }

void SBVMRangeList::Clear() { m_opaque_up.reset(); }

const SBVMRangeList &SBVMRangeList::operator=(const SBVMRangeList &rhs) {
  if (this != &rhs) {
    if (rhs.IsValid())
      m_opaque_up = std::make_unique<VMRangeListImpl>(*rhs);
    else
      m_opaque_up.reset();
  }
  return *this;
}

VMRangeListImpl *SBVMRangeList::operator->() { return m_opaque_up.get(); }

VMRangeListImpl &SBVMRangeList::operator*() { return *m_opaque_up; }

const VMRangeListImpl *SBVMRangeList::operator->() const {
  return m_opaque_up.get();
}

const VMRangeListImpl &SBVMRangeList::operator*() const { return *m_opaque_up; }

void SBVMRangeList::Append(const SBVMRange &val_obj) {
  CreateIfNeeded();
  m_opaque_up->Append(val_obj);
}

void SBVMRangeList::Append(lldb::VMRangeSP &vmrange_sp) {
  if (vmrange_sp) {
    CreateIfNeeded();
    m_opaque_up->Append(SBVMRange(vmrange_sp));
  }
}

void SBVMRangeList::Append(const lldb::SBVMRangeList &value_list) {
  if (value_list.IsValid()) {
    CreateIfNeeded();
    m_opaque_up->Append(*value_list);
  }
}

SBVMRange SBVMRangeList::GetValueAtIndex(uint32_t idx) const {
  SBVMRange sb_value;
  if (m_opaque_up)
    sb_value = m_opaque_up->GetValueAtIndex(idx);

  return sb_value;
}

uint32_t SBVMRangeList::GetSize() const {
  uint32_t size = 0;
  if (m_opaque_up)
    size = m_opaque_up->GetSize();

  return size;
}

void SBVMRangeList::CreateIfNeeded() {
  if (m_opaque_up == nullptr)
    m_opaque_up = std::make_unique<VMRangeListImpl>();
}

void *SBVMRangeList::opaque_ptr() { return m_opaque_up.get(); }

VMRangeListImpl &SBVMRangeList::ref() {
  CreateIfNeeded();
  return *m_opaque_up;
}
