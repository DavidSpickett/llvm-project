//===-- SWIG Interface for SBVMRange ----------------------------*- C++ -*-===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//

namespace lldb {

%feature("docstring",
"TODO: doc me!"
) SBVMRange;
class SBVMRange
{
public:

    SBVMRange ();

    SBVMRange (const lldb::SBVMRange &rhs);

    ~SBVMRange ();

    lldb::SBAddress
    GetBaseAddress ();

    lldb::SBAddress
    GetEndAddress ();

    // TODO: operator == and != ???

    bool
    IsValid() const;

    // TODO: clear()?

    void
    SetBaseAddress (const lldb::SBAddress &addr);

    void
    SetEndAddress (const lldb::SBAddress &addr);

    STRING_EXTENSION(SBVMRange)

};

} // namespace lldb
