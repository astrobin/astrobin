import { Pipe, PipeTransform } from "@angular/core";
import { UserInterface } from "@shared/interfaces/user.interface";

@Pipe({
  name: "isSuperUser"
})
export class IsSuperUserPipe implements PipeTransform {
  transform(user: UserInterface, args?: any): any {
    return user.isSuperUser;
  }
}
