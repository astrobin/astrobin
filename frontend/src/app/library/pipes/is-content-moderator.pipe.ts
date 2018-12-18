import { Pipe, PipeTransform } from '@angular/core';
import { UserProfileModel } from "../models/common/userprofile.model";

@Pipe({
  name: 'isContentModerator'
})
export class IsContentModeratorPipe implements PipeTransform {
  transform(value: UserProfileModel, args?: any): any {
    if(!value.userObject) {
      return false;
    }
    return value.userObject.isInGroup("content_moderators");
  }
}
