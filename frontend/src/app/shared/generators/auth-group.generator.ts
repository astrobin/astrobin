import { AuthGroupInterface } from "@shared/interfaces/auth-group.interface";

export class AuthGroupGenerator {
  static group(): AuthGroupInterface {
    return {
      id: 1,
      name: "Test group",
      permissions: []
    };
  }
}
