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
#include "lldb/Target/RegisterFlags.h"
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

void RegisterTypeBuilderClang::Terminate() {
  printf("terminate!\n");
}

lldb::RegisterTypeBuilderSP RegisterTypeBuilderClang::CreateInstance() {
  return std::make_shared<RegisterTypeBuilderClang>();
}

CompilerType RegisterTypeBuilderClang::GetRegisterType(
    const std::string &name, const lldb_private::RegisterFlags &flags,
    uint32_t byte_size) {
  std::string register_type_name = "__lldb_register_fields_" + name;
  // See if we have made this type before and can reuse it.
  CompilerType fields_type =
      m_ast->GetTypeForIdentifier<clang::CXXRecordDecl>(register_type_name);

  if (!fields_type) {
    // In most ABI, a change of field type means a change in storage unit.
    // We want it all in one unit, so we use a field type the same as the
    // register's size.
    CompilerType field_uint_type = m_ast->GetBuiltinTypeForEncodingAndBitSize(
        lldb::eEncodingUint, byte_size * 8);

    fields_type = m_ast->CreateRecordType(
        nullptr, OptionalClangModuleID(), lldb::eAccessPublic,
        register_type_name, llvm::to_underlying(clang::TagTypeKind::Struct),
        lldb::eLanguageTypeC);
    m_ast->StartTagDeclarationDefinition(fields_type);

    // We assume that RegisterFlags has padded and sorted the fields
    // already.
    for (const RegisterFlags::Field &field : flags.GetFields()) {
      CompilerType field_type = field_uint_type;

      if (const FieldEnum *enum_type = field.GetEnum()) {
        const FieldEnum::Enumerators &enumerators = enum_type->GetEnumerators();
        if (!enumerators.empty()) {
          // Enums can be used by many registers and the size of each register
          // may be different. The register size is used as the underlying size
          // of the enumerators, so we must make one enum type per register size
          // it is used with.
          std::string enum_type_name = "__lldb_register_fields_enum_" +
                                       enum_type->GetID() + "_" +
                                       std::to_string(byte_size);

          // Enums can be used by mutiple fields and multiple registers, so we
          // may have built this one already.
          CompilerType field_enum_type =
              m_ast->GetTypeForIdentifier<clang::EnumDecl>(enum_type_name);

          if (field_enum_type)
            field_type = field_enum_type;
          else {
            field_type = m_ast->CreateEnumerationType(
                enum_type_name, m_ast->GetTranslationUnitDecl(),
                OptionalClangModuleID(), Declaration(), field_uint_type, false);

            m_ast->StartTagDeclarationDefinition(field_type);

            Declaration decl;
            for (auto enumerator : enumerators) {
              m_ast->AddEnumerationValueToEnumerationType(
                  field_type, decl, enumerator.m_name.c_str(),
                  enumerator.m_value, byte_size * 8);
            }

            m_ast->CompleteTagDeclarationDefinition(field_type);
          }
        }
      }

      m_ast->AddFieldToRecordType(fields_type, field.GetName(), field_type,
                                  lldb::eAccessPublic, field.GetSizeInBits());
    }

    m_ast->CompleteTagDeclarationDefinition(fields_type);
    // So that the size of the type matches the size of the register.
    m_ast->SetIsPacked(fields_type);

    // This should be true if RegisterFlags padded correctly.
    assert(*fields_type.GetByteSize(nullptr) == flags.GetSize());
  }

  assert(fields_type.IsValid());

  return fields_type;
}
