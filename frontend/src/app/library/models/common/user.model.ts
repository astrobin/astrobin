import { GroupModel } from "./group.model";

export class UserModel {
  id: number;
  avatar?: string;
  last_login?: Date;
  is_superuser: boolean;
  username: string;
  first_name?: string;
  is_staff: boolean;
  is_active: boolean;
  date_joined: Date;
  groups: GroupModel[];

  constructor(values: Object = {}) {
    Object.assign(this, values);
  }

  isInGroup(name: string): boolean {
    if (!this.groups) {
      return false;
    }
    return this.groups.filter(group => group.name === name).length > 0;
  }
}
