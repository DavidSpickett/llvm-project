//===-- RegisterTypeBuilderClang.cpp ---------------------------===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//

#include "clang/AST/DeclCXX.h"

#include "Plugins/TypeSystem/Clang/TypeSystemClang.h"
#include "RegisterTypeBuilderClang.h"
#include "lldb/Core/PluginManager.h"
#include "lldb/Target/RegisterTypeFlags.h"
#include "lldb/lldb-enumerations.h"

using namespace lldb_private;

LLDB_PLUGIN_DEFINE(RegisterTypeBuilderClang)

void RegisterTypeBuilderClang::Initialize() {
  static llvm::once_flag g_once_flag;
  llvm::call_once(g_once_flag, []() {
    PluginManager::RegisterPlugin(GetPluginNameStatic(),
                                  GetPluginDescriptionStatic(), CreateInstance);
  });
}

void RegisterTypeBuilderClang::Terminate() {}

lldb::RegisterTypeBuilderSP
RegisterTypeBuilderClang::CreateInstance(Target &target) {
  return std::make_shared<RegisterTypeBuilderClang>(target);
}

RegisterTypeBuilderClang::RegisterTypeBuilderClang(Target &target)
    : m_target(target) {}

static std::string MakeTypeName(const RegisterType &type_info,
                                uint32_t register_byte_size) {
  std::string type_name = "__lldb_register_fields_";
  switch (type_info.getKind()) {
  case RegisterType::eRegisterTypeKindFlags:
    type_name += "flags_";
    break;
  case RegisterType::eRegisterTypeKindUnion:
    type_name += "union_";
    break;
  case RegisterType::eRegisterTypeKindEnum:
    // Enums can be used by many registers and the size of each register
    // may be different. The register size is used as the underlying size
    // of the enumerators, so we must make one enum type per register size
    // it is used with.
    type_name += "enum_" + std::to_string(register_byte_size) + "_";
    break;
  }

  return type_name + type_info.GetID();
}

static CompilerType BuildEnumType(const RegisterTypeEnum &enum_type_info,
                                  uint32_t register_byte_size,
                                  lldb::TypeSystemClangSP type_system) {
  std::string enum_type_name = MakeTypeName(enum_type_info, register_byte_size);

  // Reuse existing type if we can.
  if (CompilerType enum_type =
          type_system->GetTypeForIdentifier<clang::EnumDecl>(enum_type_name))
    return enum_type;

  CompilerType register_uint_type =
      type_system->GetBuiltinTypeForEncodingAndBitSize(lldb::eEncodingUint,
                                                       register_byte_size * 8);
  CompilerType enum_type = type_system->CreateEnumerationType(
      enum_type_name, type_system->GetTranslationUnitDecl(),
      OptionalClangModuleID(), Declaration(), register_uint_type, false);

  type_system->StartTagDeclarationDefinition(enum_type);

  Declaration decl;
  for (const auto &enumerator : enum_type_info.GetEnumerators()) {
    type_system->AddEnumerationValueToEnumerationType(
        enum_type, decl, enumerator.m_name.c_str(), enumerator.m_value,
        register_byte_size * 8);
  }

  type_system->CompleteTagDeclarationDefinition(enum_type);

  return enum_type;
}

static CompilerType
BuildFlagsType(const lldb_private::RegisterTypeFlags &flags_info,
               uint32_t register_byte_size,
               lldb::TypeSystemClangSP type_system) {
  std::string register_type_name = MakeTypeName(flags_info, register_byte_size);

  // Reuse existing type if we can.
  if (CompilerType flags_type =
          type_system->GetTypeForIdentifier<clang::CXXRecordDecl>(
              register_type_name))
    return flags_type;

  // In most ABI, a change of field type means a change in storage unit.
  // We want it all in one unit, so we use a field type the same as the
  // register's size.
  CompilerType field_uint_type =
      type_system->GetBuiltinTypeForEncodingAndBitSize(lldb::eEncodingUint,
                                                       register_byte_size * 8);

  CompilerType flags_type = type_system->CreateRecordType(
      nullptr, OptionalClangModuleID(), lldb::eAccessPublic, register_type_name,
      llvm::to_underlying(clang::TagTypeKind::Struct), lldb::eLanguageTypeC);
  type_system->StartTagDeclarationDefinition(flags_type);

  // We assume that RegisterTypeFlags has padded and sorted the fields
  // already.
  for (const RegisterTypeFlags::Field &field : flags_info.GetFields()) {
    CompilerType field_type = field_uint_type;

    if (const RegisterTypeEnum *enum_type_info = field.GetEnum())
      if (!enum_type_info->GetEnumerators().empty())
        field_type =
            BuildEnumType(*enum_type_info, register_byte_size, type_system);

    type_system->AddFieldToRecordType(flags_type, field.GetName(), field_type,
                                      lldb::eAccessPublic,
                                      field.GetSizeInBits());
  }

  type_system->CompleteTagDeclarationDefinition(flags_type);
  // So that the size of the type matches the size of the register.
  type_system->SetIsPacked(flags_type);

  // This should be true if RegisterTypeFlags padded correctly.
  assert(*flags_type.GetByteSize(nullptr) == flags_info.GetSize());

  return flags_type;
}

CompilerType RegisterTypeBuilderClang::GetRegisterType(
    const lldb_private::RegisterType &type_info, uint32_t register_byte_size) {
  lldb::TypeSystemClangSP type_system =
      ScratchTypeSystemClang::GetForTarget(m_target);
  assert(type_system);

  switch (type_info.getKind()) {
  case RegisterType::eRegisterTypeKindFlags:
    return BuildFlagsType(*llvm::dyn_cast<RegisterTypeFlags>(&type_info),
                          register_byte_size, type_system);
  case RegisterType::eRegisterTypeKindUnion:
    return {};
  case RegisterType::eRegisterTypeKindEnum:
    return {};
  }
}
