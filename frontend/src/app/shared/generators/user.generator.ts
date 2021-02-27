import { AuthGroupGenerator } from "@shared/generators/auth-group.generator";
import { UserInterface } from "@shared/interfaces/user.interface";

export class UserGenerator {
  static user(): UserInterface {
    return {
      id: 1,
      userProfile: 1,
      username: "Test",
      firstName: "Test",
      avatar: null,
      lastLogin: new Date("2010-01-01"),
      dateJoined: new Date("2010-01-01"),
      isSuperUser: false,
      isStaff: false,
      isActive: true,
      groups: [AuthGroupGenerator.group()],
      userPermissions: []
    };
  }
}
