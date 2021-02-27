import { PermissionInterface } from "@shared/interfaces/permission.interface";

export interface GroupInterface {
  id: number;
  name: string;
  permissions?: PermissionInterface[];
}
