//===-- SWIG Interface for SBMemoryTagManager -------------------*- C++ -*-===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//

namespace lldb {

%feature("docstring",
"TODO: doc me!"
) SBMemoryTagManager;
class SBMemoryTagManager
{
public:

    SBMemoryTagManager ();

    SBMemoryTagManager (const lldb::SBMemoryTagManager &rhs);

    ~SBMemoryTagManager ();

    bool IsValid() const;

    bool GetDescription(lldb::SBStream &description);

    const char *GetTagTypeName();

    // TODO: do we want to name this differently in case of different read/write types?
    int GetAllocationTagType();

    addr_t GetGranuleSize() const;

    lldb::SBError MakeTaggedRange(int32_t type,
                                const lldb::SBVMRange &range,
                                const lldb::SBMemoryRegionInfoList &regions,
                                lldb::SBVMRange &result);

    lldb::SBError MakeTaggedRanges(int32_t type, const lldb::SBVMRange &range,
                   const lldb::SBMemoryRegionInfoList &regions,
                   lldb::SBVMRangeList &result) const;

    STRING_EXTENSION(SBMemoryTagManager)

};

} // namespace lldb
