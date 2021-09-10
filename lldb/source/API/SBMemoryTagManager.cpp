//===-- SBMemoryTagManager.cpp --------------------------------------------===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//

#include "lldb/API/SBMemoryTagManager.h"
#include "lldb/API/SBAddress.h"
#include "lldb/API/SBMemoryRegionInfo.h"
#include "lldb/API/SBStream.h"
#include "lldb/Utility/Stream.h"

using namespace lldb;
using namespace lldb_private;

SBMemoryTagManager::SBMemoryTagManager() {}

SBMemoryTagManager::SBMemoryTagManager(const SBMemoryTagManager &rhs) {
  m_opaque_ptr = rhs.m_opaque_ptr;
}

SBMemoryTagManager::SBMemoryTagManager(
    const lldb_private::MemoryTagManager *tag_manager_ptr)
    : m_opaque_ptr(tag_manager_ptr) {}

const SBMemoryTagManager &
SBMemoryTagManager::operator=(const SBMemoryTagManager &rhs) {
  if (this != &rhs)
    m_opaque_ptr = rhs.m_opaque_ptr;
  return *this;
}

SBMemoryTagManager::~SBMemoryTagManager() = default;

bool SBMemoryTagManager::IsValid() const { return this->operator bool(); }
SBMemoryTagManager::operator bool() const { return m_opaque_ptr != nullptr; }

const lldb_private::MemoryTagManager *SBMemoryTagManager::GetPtr() const {
  return m_opaque_ptr;
}

void SBMemoryTagManager::SetPtr(
    const lldb_private::MemoryTagManager *tag_manager_ptr) {
  m_opaque_ptr = tag_manager_ptr;
}

bool SBMemoryTagManager::GetDescription(SBStream &description) {
  // Call "ref()" on the stream to make sure it creates a backing stream in
  // case there isn't one already...
  Stream &strm = description.ref();
  if (m_opaque_ptr) {
    m_opaque_ptr->Dump(&strm);
  } else
    strm.PutCString("No memory tag manager set");

  return true;
}

const char *SBMemoryTagManager::GetTagTypeName() const {
  // TODO: ok to do this check here?
  return m_opaque_ptr ? m_opaque_ptr->GetTagTypeName().AsCString() : nullptr;
}

int SBMemoryTagManager::GetAllocationTagType() const {
  // TODO: how do we cope with invalid tag manager here?
  // Since -1 is a valid tag type.
  return m_opaque_ptr->GetAllocationTagType();
}

addr_t SBMemoryTagManager::GetGranuleSize() const {
  // TODO: how do we cope with invalid tag manager here?
  return m_opaque_ptr->GetGranuleSize();
}

lldb::SBError
SBMemoryTagManager::MakeTaggedRange(int32_t type, const lldb::SBVMRange &range,
                                    const lldb::SBMemoryRegionInfoList &regions,
                                    lldb::SBVMRange &result) const {
  SBError sb_err;

  if (!range.IsValid()) {
    sb_err.SetErrorString("Intitial range must be valid.");
    return sb_err;
  }

  if (!m_opaque_ptr) {
    sb_err.SetErrorString("Cannot call this method on an invalid tag manager.");
    return sb_err;
  }

  // For now tag type to manager is 1:1 but this could change later
  if (type != m_opaque_ptr->GetAllocationTagType()) {
    sb_err.SetErrorString("Tag type not supported by this tag manager.");
    return sb_err;
  }

  llvm::Expected<MemoryTagManager::TagRange> tagged_range_or_err =
      m_opaque_ptr->MakeTaggedRange(range.GetBaseAddress().GetFileAddress(),
                                    range.GetEndAddress().GetFileAddress(),
                                    regions.ref());

  if (!tagged_range_or_err) {
    sb_err.SetErrorString(toString(tagged_range_or_err.takeError()).c_str());
    return sb_err;
  }

  MemoryTagManager::TagRange tagged_range = *tagged_range_or_err;
  SBAddress start_addr(lldb::SBSection(), tagged_range.GetRangeBase());
  result.SetBaseAddress(start_addr);
  SBAddress end_addr(lldb::SBSection(), tagged_range.GetRangeEnd());
  result.SetEndAddress(end_addr);

  return sb_err;
}

lldb::SBError SBMemoryTagManager::MakeTaggedRanges(
    int32_t type, const lldb::SBVMRange &range,
    const lldb::SBMemoryRegionInfoList &regions,
    lldb::SBVMRangeList &result) const {
  SBError sb_err;

  // TODO: dedupe all this validity checking?
  if (!range.IsValid()) {
    sb_err.SetErrorString("Intitial range must be valid.");
    return sb_err;
  }

  if (!m_opaque_ptr) {
    sb_err.SetErrorString("Cannot call this method on an invalid tag manager.");
    return sb_err;
  }

  // For now tag type to manager is 1:1 but this could change later
  if (type != m_opaque_ptr->GetAllocationTagType()) {
    sb_err.SetErrorString("Tag type not supported by this tag manager.");
    return sb_err;
  }

  // MemoryTagManager proper asserts that all regions are sorted and do not
  // overlap. Here in the API we can't crash to check before calling the real
  // method and error if so.

  // TODO: test this!
  auto regions_ref = regions.ref();
  if (!std::is_sorted(
          regions_ref.begin(), regions_ref.end(),
          [](const MemoryRegionInfo &lhs, const MemoryRegionInfo &rhs) {
            return lhs.GetRange().GetRangeBase() <
                   rhs.GetRange().GetRangeBase();
          })) {
    sb_err.SetErrorString(
        "Memory regions must be sorted in ascending order by start address.");
    return sb_err;
  }

  // TODO: test this!
  if (std::adjacent_find(
          regions_ref.begin(), regions_ref.end(),
          [](const MemoryRegionInfo &lhs, const MemoryRegionInfo &rhs) {
            return rhs.GetRange().DoesIntersect(lhs.GetRange());
          }) != regions_ref.end()) {
    sb_err.SetErrorString("Memory regions must not overlap.");
    return sb_err;
  }

  llvm::Expected<std::vector<MemoryTagManager::TagRange>> tagged_ranges_or_err =
      m_opaque_ptr->MakeTaggedRanges(range.GetBaseAddress().GetFileAddress(),
                                     range.GetEndAddress().GetFileAddress(),
                                     regions.ref());

  if (!tagged_ranges_or_err) {
    sb_err.SetErrorString(toString(tagged_ranges_or_err.takeError()).c_str());
    return sb_err;
  }

  std::vector<MemoryTagManager::TagRange> tagged_ranges = *tagged_ranges_or_err;
  for (const MemoryTagManager::TagRange &tagged_range : tagged_ranges) {
    SBAddress start_addr(lldb::SBSection(), tagged_range.GetRangeBase());
    SBAddress end_addr(lldb::SBSection(), tagged_range.GetRangeEnd());
    SBVMRange sb_tagged_range;
    sb_tagged_range.SetBaseAddress(start_addr);
    sb_tagged_range.SetEndAddress(end_addr);
    result.Append(sb_tagged_range);
  }

  return sb_err;
}
