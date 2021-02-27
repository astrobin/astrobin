import { Pipe, PipeTransform } from "@angular/core";
import { environment } from "@env/environment.prod";

@Pipe({
  name: "normalizeNotificationLink"
})
export class NormalizeNotificationLinkPipe implements PipeTransform {
  transform(value: string): string {
    return value.replace(/href="\//g, `href="${environment.classicBaseUrl}/`);
  }
}
