import { PermissionInterface } from "@shared/interfaces/permission.interface";

export interface AuthGroupInterface {
  id: number;
  name: string;
  permissions?: PermissionInterface[];
}
