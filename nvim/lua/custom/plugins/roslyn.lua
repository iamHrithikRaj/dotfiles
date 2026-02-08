-- Roslyn.nvim — C# LSP using Microsoft's Roslyn compiler
-- This is the same compiler engine that powers Visual Studio and VS Code's C# extension.
-- Much better for large .NET solutions and monorepos than OmniSharp.
--
-- REQUIREMENTS:
--   - .NET SDK must be installed (https://dotnet.microsoft.com/download)
--   - The Roslyn LSP server binary is downloaded automatically on first use
--
-- USAGE:
--   Open a .cs file inside a directory with a .sln or .csproj file.
--   Roslyn will auto-detect the solution and provide full IntelliSense.

return {
  'seblj/roslyn.nvim',
  ft = 'cs',
  opts = {
    -- Filetypes that trigger Roslyn LSP activation
    filewatching = true,

    config = {
      settings = {
        ['csharp|inlay_hints'] = {
          csharp_enable_inlay_hints_for_implicit_object_creation = true,
          csharp_enable_inlay_hints_for_implicit_variable_types = true,
          csharp_enable_inlay_hints_for_lambda_parameter_types = true,
          csharp_enable_inlay_hints_for_types = true,
          dotnet_enable_inlay_hints_for_indexer_parameters = true,
          dotnet_enable_inlay_hints_for_literal_parameters = true,
          dotnet_enable_inlay_hints_for_object_creation_parameters = true,
          dotnet_enable_inlay_hints_for_other_parameters = true,
          dotnet_enable_inlay_hints_for_parameters = true,
          dotnet_suppress_inlay_hints_for_parameters_that_differ_only_by_suffix = true,
          dotnet_suppress_inlay_hints_for_parameters_that_match_argument_name = true,
          dotnet_suppress_inlay_hints_for_parameters_that_match_method_intent = true,
        },
        ['csharp|code_lens'] = {
          dotnet_enable_references_code_lens = true,
          dotnet_enable_tests_code_lens = true,
        },
      },
    },
  },
}
