import { Injectable } from "@angular/core";
import { UsernameServiceInterface } from "@shared/components/misc/username/username.service-interface";
import { UserInterface } from "@shared/interfaces/user.interface";
import { BaseService } from "@shared/services/base.service";
import { LoadingService } from "@shared/services/loading.service";
import { UserStoreService } from "@shared/services/user-store.service";

@Injectable()
export class UsernameService extends BaseService implements UsernameServiceInterface {
  constructor(public loadingService: LoadingService, public userStore: UserStoreService) {
    super(loadingService);
  }

  getDisplayName(user: UserInterface): string {
    if (!user) {
      return "";
    }

    const userProfile = this.userStore.getUserProfile(user.userProfile);

    if (userProfile && userProfile.realName) {
      return userProfile.realName;
    }

    return user.username;
  }
}
