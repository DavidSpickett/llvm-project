//===-- SWIG Interface for SBVMRangeList -------------------------*- C++ -*-===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//

namespace lldb {

%feature("docstring",
"TODO: doc me like SBValueList
"
) SBVMRangeList;
class SBVMRangeList
{
public:

    SBVMRangeList ();

    SBVMRangeList (const lldb::SBVMRangeList &rhs);

    ~SBVMRangeList();

    bool
    IsValid() const;

    explicit operator bool() const;

    void
    Clear();

    void
    Append (const lldb::SBVMRange &range_obj);

    void
    Append (const lldb::SBVMRangeList& range_list);

    uint32_t
    GetSize() const;

    lldb::SBVMRange
    GetValueAtIndex (uint32_t idx) const;

    // TODO: still works?
    %extend {
       %nothreadallow;
       std::string lldb::SBVMRangeList::__str__ (){
           lldb::SBStream description;
           const size_t n = $self->GetSize();
           if (n)
           {
               for (size_t i=0; i<n; ++i)
                   $self->GetValueAtIndex(i).GetDescription(description);
           }
           else
           {
               description.Printf("<empty> lldb.SBVMRangeList()");
           }
           const char *desc = description.GetData();
           size_t desc_len = description.GetSize();
           if (desc_len > 0 && (desc[desc_len-1] == '\n' || desc[desc_len-1] == '\r'))
               --desc_len;
           return std::string(desc, desc_len);
       }
       %clearnothreadallow;
    }

// TODO: still works?
#ifdef SWIGPYTHON
    %pythoncode %{
        def __iter__(self):
            '''Iterate over all values in a lldb.SBVMRangeList object.'''
            return lldb_iter(self, 'GetSize', 'GetValueAtIndex')

        def __len__(self):
            return int(self.GetSize())

        def __getitem__(self, key):
            count = len(self)
            #------------------------------------------------------------
            # Access with "int" to get Nth item in the list
            #------------------------------------------------------------
            if type(key) is int:
                if key < count:
                    return self.GetValueAtIndex(key)
            # TODO: need to raise something here?
    %}
#endif


};

} // namespace lldb
