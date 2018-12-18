import { Pipe, PipeTransform } from '@angular/core';
import { UserProfileModel } from "../models/common/userprofile.model";

@Pipe({
  name: 'isIotdSubmitter'
})
export class IsIotdSubmitterPipe implements PipeTransform {
  transform(value: UserProfileModel, args?: any): any {
    if(!value.userObject) {
      return false;
    }
    return value.userObject.isInGroup("iotd_submitters");
  }
}
