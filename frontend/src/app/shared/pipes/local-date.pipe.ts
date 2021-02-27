import { Pipe, PipeTransform } from "@angular/core";

@Pipe({
  name: "localDate"
})
export class LocalDatePipe implements PipeTransform {
  transform(value: string): Date {
    if (value.charAt(value.length - 1) !== "Z") {
      value += "Z";
    }

    return new Date(value);
  }
}
