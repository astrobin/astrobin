import { Pipe, PipeTransform } from '@angular/core';
import { UserProfileModel } from "../models/common/userprofile.model";

@Pipe({
  name: 'isSuperuser'
})
export class IsSuperuserPipe implements PipeTransform {
  transform(value: UserProfileModel, args?: any): any {
    if (!value.userObject) {
      return false;
    }
    return value.userObject.is_superuser;
  }
}
