//===-- SBMemoryTagManagerList.h --------------------------------*- C++ -*-===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//

namespace lldb {

%feature("docstring",
"Represents a list of :py:class:`SBMemoryTagManager`."
) SBMemoryTagManagerList;
class SBMemoryTagManagerList
{
public:

    SBMemoryTagManagerList ();

    SBMemoryTagManagerList (const lldb::SBMemoryTagManagerList &rhs);

    ~SBMemoryTagManagerList ();

    uint32_t
    GetSize () const;

    bool
    GetMemoryTagManagerAtIndex (uint32_t idx, SBMemoryTagManager &tag_manager);

    void
    Append (lldb::SBMemoryTagManager &region);

    void
    Append (lldb::SBMemoryTagManagerList &region_list);

    void
    Clear ();
};

} // namespace lldb
