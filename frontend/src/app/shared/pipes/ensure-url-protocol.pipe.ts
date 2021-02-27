import { Pipe, PipeTransform } from "@angular/core";

@Pipe({
  name: "ensureUrlProtocol"
})
export class EnsureUrlProtocolPipe implements PipeTransform {
  transform(value: string, args?: any): string {
    if (value.indexOf("://") === -1) {
      return `http://${value}`;
    }

    return value;
  }
}
