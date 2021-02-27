import { Injectable } from "@angular/core";
import { UserProfileInterface } from "@shared/interfaces/user-profile.interface";
import { UserInterface } from "@shared/interfaces/user.interface";
import { BaseService } from "@shared/services/base.service";
import { UserStoreServiceInterface } from "@shared/services/user-store.service-interface";

@Injectable({
  providedIn: "root"
})
export class UserStoreService extends BaseService implements UserStoreServiceInterface {
  private _users: { [key: number]: UserInterface } = {};
  private _userProfiles: { [key: number]: UserProfileInterface } = {};

  addUser(user: UserInterface): void {
    this._users[user.id] = user;
  }

  addUserProfile(userProfile: UserProfileInterface): void {
    this._userProfiles[userProfile.id] = userProfile;
  }

  getUser(id: number): UserInterface {
    return this._users[id];
  }

  getUserProfile(id: number): UserProfileInterface {
    return this._userProfiles[id];
  }
}
