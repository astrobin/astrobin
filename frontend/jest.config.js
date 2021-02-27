const { pathsToModuleNameMapper } = require("ts-jest/utils");
const { compilerOptions } = require("./tsconfig.json");

module.exports = {
  verbose: true,
  preset: "jest-preset-angular",
  setupFilesAfterEnv: ["<rootDir>/setupJest.ts"],
  collectCoverageFrom: ["**/*.ts", "!main.ts", "!**/*.module.(t|j)s", "!**/*mock.ts", "!**/*routing.ts"],
  coverageDirectory: "coverage",
  transformIgnorePatterns: ["^.+\\.js$"],
  moduleNameMapper: pathsToModuleNameMapper(compilerOptions.paths, { prefix: "<rootDir>/" }),
  modulePathIgnorePatterns: ["<rootDir>/cypress"],
  globals: {
    "ts-jest": {
      tsconfig: "<rootDir>/src/tsconfig.spec.json"
    }
  }
};
