import { Component, Input } from "@angular/core";
import { TranslateService } from "@ngx-translate/core";
import { SolutionInterface } from "@shared/interfaces/solution.interface";
import { SolutionService } from "@shared/services/solution/solution.service";

@Component({
  selector: "astrobin-objects-in-field",
  templateUrl: "./objects-in-field.component.html",
  styleUrls: ["./objects-in-field.component.scss"]
})
export class ObjectsInFieldComponent {
  @Input()
  solution: SolutionInterface;

  constructor(public readonly solutionService: SolutionService, public readonly translateService: TranslateService) {}

  get objectsInField(): string {
    const objects = this.solutionService.getObjectsInField(this.solution);
    let value;

    if (!!objects) {
      value = objects.join(", ");
    }

    if (!value) {
      value = this.translateService.instant("n/a");
    }

    return value;
  }
}
