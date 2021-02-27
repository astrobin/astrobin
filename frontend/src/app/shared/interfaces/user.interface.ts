import { AuthGroupInterface } from "@shared/interfaces/auth-group.interface";
import { PermissionInterface } from "@shared/interfaces/permission.interface";

export interface UserInterface {
  id: number;
  userProfile: number;
  username: string;
  firstName: string;
  avatar: string;
  lastLogin: Date;
  dateJoined: Date;
  isSuperUser: boolean;
  isStaff: boolean;
  isActive: boolean;
  groups: AuthGroupInterface[];
  userPermissions: PermissionInterface[];
}
