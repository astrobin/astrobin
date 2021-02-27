import { UserProfileInterface } from "@shared/interfaces/user-profile.interface";
import { UserInterface } from "@shared/interfaces/user.interface";

export interface UserStoreServiceInterface {
  addUser(user: UserInterface): void;

  addUserProfile(userProfile: UserProfileInterface): void;

  getUser(id: number): UserInterface;

  getUserProfile(id: number): UserProfileInterface;
}
