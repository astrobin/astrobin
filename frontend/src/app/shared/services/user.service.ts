import { Injectable } from "@angular/core";
import { AuthGroupInterface } from "@shared/interfaces/auth-group.interface";
import { UserInterface } from "@shared/interfaces/user.interface";
import { BaseService } from "@shared/services/base.service";
import { UserServiceInterface } from "@shared/services/user.service-interface";

@Injectable({
  providedIn: "root"
})
export class UserService extends BaseService implements UserServiceInterface {
  isInGroup(user: UserInterface, name: string): boolean {
    if (!user || !user.groups) {
      return false;
    }
    return user.groups.filter((group: AuthGroupInterface) => group.name === name).length > 0;
  }
}
