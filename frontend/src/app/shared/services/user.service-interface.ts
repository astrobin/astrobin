import { UserInterface } from "@shared/interfaces/user.interface";

export interface UserServiceInterface {
  isInGroup(user: UserInterface, name: string): boolean;
}
