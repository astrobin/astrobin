import { UserInterface } from "@shared/interfaces/user.interface";

export interface UsernameServiceInterface {
  getDisplayName(user: UserInterface): string;
}
