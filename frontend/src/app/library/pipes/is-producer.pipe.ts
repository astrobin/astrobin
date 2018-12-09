import { Pipe, PipeTransform } from '@angular/core';
import { UserProfileModel } from "../models/common/userprofile.model";

@Pipe({
  name: 'isProducer'
})
export class IsProducerPipe implements PipeTransform {

  transform(value: UserProfileModel, args?: any): any {
    if(!value.userObject) {
      return false;
    }
    return value.userObject.isInGroup("Producers");
  }

}
