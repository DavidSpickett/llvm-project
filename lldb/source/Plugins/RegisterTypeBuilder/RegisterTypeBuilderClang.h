//===-- RegisterTypeBuilderClang.h ------------------------------*- C++ -*-===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//

#ifndef LLDB_PLUGINS_REGISTERTYPEBUILDER_REGISTERTYPEBUILDERCLANG_H
#define LLDB_PLUGINS_REGISTERTYPEBUILDER_REGISTERTYPEBUILDERCLANG_H

#include "lldb/Target/RegisterTypeBuilder.h"
#include "Plugins/TypeSystem/Clang/TypeSystemClang.h"

namespace lldb_private {
class TypeSystemClangHolder {
  std::shared_ptr<TypeSystemClang> m_ast;

public:
  TypeSystemClangHolder()
      : m_ast(std::make_shared<TypeSystemClang>(
            "registers",
            // TODO: what if aarch64 isn't built in?
            llvm::Triple("aarch64_be-none-elf"))) {}
  TypeSystemClang *GetAST() const { return m_ast.get(); }
};

class RegisterTypeBuilderClang : public RegisterTypeBuilder {
public:
  RegisterTypeBuilderClang()
      : m_holder(std::make_unique<TypeSystemClangHolder>()),
        m_ast(m_holder->GetAST()) {}

  static void Initialize();
  static void Terminate();
  static llvm::StringRef GetPluginNameStatic() {
    return "register-types-clang";
  }
  llvm::StringRef GetPluginName() override { return GetPluginNameStatic(); }
  static llvm::StringRef GetPluginDescriptionStatic() {
    return "Create register types using TypeSystemClang";
  }
  static lldb::RegisterTypeBuilderSP CreateInstance();

  CompilerType GetRegisterType(const std::string &name,
                               const lldb_private::RegisterFlags &flags,
                               uint32_t byte_size) override;

private:
  std::unique_ptr<TypeSystemClangHolder> m_holder;
  TypeSystemClang *m_ast = nullptr;
};
} // namespace lldb_private

#endif // LLDB_PLUGINS_REGISTERTYPEBUILDER_REGISTERTYPEBUILDERCLANG_H
