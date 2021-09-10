# TODO: move this into proper tests and delete this file!

from lldb import process, SBVMRange, SBStringList, SBAddress, SBSection, SBError
from lldb import SBStructuredData, SBMemoryTagManager, SBStream, SBVMRangeList
import json

def check_err(err):
    if err:
        raise RuntimeError(str(err))

def make_range(start, end):
    start_addr = SBAddress()
    start_addr.SetAddress(SBSection(), start)
    end_addr = SBAddress()
    end_addr.SetAddress(SBSection(), end)

    ret = SBVMRange()
    ret.SetBaseAddress(start_addr)
    ret.SetEndAddress(end_addr)

    return ret

def get_tagged_range(process, manager, tag_type, start, end):
    wanted = make_range(start, end)
    got = SBVMRange()
    regions = process.GetMemoryRegions()

    err = manager.MakeTaggedRange(tag_type, wanted, regions, got)
    check_err(err)

    return got

def write_tags(process, manager, tag_type, start, end, tags):
    tagged_range = get_tagged_range(process, manager, tag_type, start, end)

    tag_data = SBStructuredData()
    # TODO: Would be nice if we had a more specific way to set this
    # Also, do we need to be able to set tags that are more than just a number?
    tag_data.SetFromJSON(json.dumps(tags))
    err = process.WriteMemoryTags(tag_type, tagged_range, tag_data)
    check_err(err)

def read_tags(process, manager, tag_type, start, end):
    tagged_range = get_tagged_range(process, manager, tag_type, start, end)

    result = SBStructuredData()
    err = process.ReadMemoryTags(tag_type, tagged_range, result)
    check_err(err)

    ret = []
    for i in range(result.GetSize()):
        ret.append(result.GetItemAtIndex(i).GetIntegerValue())
    return ret

def best_effort_read_tags(process, manager, tag_type, start, end):
    wanted = make_range(start, end)
    got = SBVMRangeList()
    regions = process.GetMemoryRegions()
    err = manager.MakeTaggedRanges(tag_type, wanted, regions, got)
    check_err(err)

    ret = []
    for i in range(got.GetSize()):
      result = SBStructuredData()
      # Should this be GetItem instead?
      tagged_range = got.GetValueAtIndex(i)
      err = process.ReadMemoryTags(tag_type, tagged_range, result)
      check_err(err)

      for i in range(result.GetSize()):
          ret.append(result.GetItemAtIndex(i).GetIntegerValue())

    return ret

def dowork():
    frame  = process.GetThreadAtIndex(0).GetFrameAtIndex(0)
    mte_buf = frame.FindVariable("mte_buf").GetValueAsUnsigned()

    # TODO: later we need better access to ABI
    err = SBError()
    mte_buf = process.FixDataAddress(mte_buf, err)
    check_err(err)

    print("mte_buf location after fixing is", hex(mte_buf))

    tag_managers = process.GetMemoryTagManagers()
    assert(tag_managers.GetSize() == 1)
    manager = SBMemoryTagManager()
    assert(tag_managers.GetMemoryTagManagerAtIndex(0, manager))
    desc = SBStream()
    assert(manager.GetDescription(desc))
    print(desc.GetData())
    print(manager.GetTagTypeName())

    granule_size = manager.GetGranuleSize()
    print("Granule size in bytes is", granule_size)

    # TODO: not sure here if we should return some structured
    # type here that doesn't hardcode "allocation" in the name
    # return dict tag type name -> number?
    tag_type = manager.GetAllocationTagType()

    start = mte_buf
    end = mte_buf+0x40

    tags = read_tags(process, manager, tag_type, start, end)
    print("Reading tags...")
    print(tags)
    print("Writing with first tag = 7...")
    tags[0] = 7
    write_tags(process, manager, tag_type, start, end, tags)
    tags = read_tags(process, manager, tag_type, start, end)
    print(tags)

    start -= 16
    print("Reading any tags from {:x} to {:x}".format(start, end))
    print("(starting from before the tagged page)")
    tags = best_effort_read_tags(process, manager, tag_type, start, end)
    print(tags)

dowork()
