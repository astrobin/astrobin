import { GroupInterface } from "@shared/interfaces/group.interface";

export class GroupGenerator {
  static group(): GroupInterface {
    return {
      id: 1,
      name: "Test group",
      permissions: []
    };
  }
}
