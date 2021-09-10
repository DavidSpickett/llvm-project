//===-- SBVMRange.cpp -----------------------------------------------------===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//

#include "lldb/API/SBVMRange.h"
#include "Utils.h"
#include "lldb/API/SBAddress.h"
#include "lldb/API/SBStream.h"
#include "lldb/Utility/Stream.h"
#include "lldb/Utility/VMRange.h"

using namespace lldb;
using namespace lldb_private;

// TODO: should you init the UP here or not? SBAddress does.
SBVMRange::SBVMRange() {}

SBVMRange::SBVMRange(const SBVMRange &rhs) {
  m_opaque_sp = clone(rhs.m_opaque_sp);
}

SBVMRange::SBVMRange(const lldb::VMRangeSP &vmrange_sp) {
  m_opaque_sp = vmrange_sp;
}

const SBVMRange &SBVMRange::operator=(const SBVMRange &rhs) {
  if (this != &rhs)
    m_opaque_sp = clone(rhs.m_opaque_sp);
  return *this;
}

SBVMRange::~SBVMRange() = default;

VMRange &SBVMRange::ref() {
  if (m_opaque_sp == nullptr)
    m_opaque_sp = std::make_unique<VMRange>();
  return *m_opaque_sp;
}

const VMRange &SBVMRange::ref() const {
  // This object should already have checked with "IsValid()" prior to calling
  // this function. In case you didn't we will assert and die to let you know.
  assert(m_opaque_sp.get());
  return *m_opaque_sp;
}

bool SBVMRange::IsValid() const { return this->operator bool(); }
SBVMRange::operator bool() const { return m_opaque_sp != nullptr; }

bool SBVMRange::GetDescription(SBStream &description) {
  // Call "ref()" on the stream to make sure it creates a backing stream in
  // case there isn't one already...
  Stream &strm = description.ref();
  if (m_opaque_sp) {
    m_opaque_sp->Dump(strm.AsRawOstream());
  } else
    strm.PutCString("No range set");

  return true;
}

lldb::SBAddress SBVMRange::GetBaseAddress() const {
  lldb::SBAddress addr;
  if (m_opaque_sp)
    addr.SetAddress(lldb::SBSection(), m_opaque_sp->GetBaseAddress());

  return addr;
}

lldb::SBAddress SBVMRange::GetEndAddress() const {
  lldb::SBAddress addr;
  if (m_opaque_sp)
    addr.SetAddress(lldb::SBSection(), m_opaque_sp->GetEndAddress());

  return addr;
}

void SBVMRange::SetBaseAddress(const lldb::SBAddress &addr) {
  // TODO: err if no ptr or invalid?
  if (addr.IsValid())
    ref().SetBaseAddress(addr.GetFileAddress());
}

void SBVMRange::SetEndAddress(const lldb::SBAddress &addr) {
  // TODO: err if no ptr or invalid?
  if (addr.IsValid())
    ref().SetEndAddress(addr.GetFileAddress());
}
