import { Pipe, PipeTransform } from "@angular/core";
import { UserInterface } from "@shared/interfaces/user.interface";
import { UserService } from "@shared/services/user.service";

@Pipe({
  name: "isContentModerator"
})
export class IsContentModeratorPipe implements PipeTransform {
  constructor(public userService: UserService) {}

  transform(user: UserInterface, args?: any): any {
    return this.userService.isInGroup(user, "content_moderators");
  }
}
