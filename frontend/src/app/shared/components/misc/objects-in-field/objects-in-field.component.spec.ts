import { ComponentFixture, TestBed } from "@angular/core/testing";
import { AppModule } from "@app/app.module";
import { SolutionGenerator } from "@shared/generators/solution.generator";
import { MockBuilder } from "ng-mocks";
import { ObjectsInFieldComponent } from "./objects-in-field.component";

describe("ObjectsInFieldComponent", () => {
  let component: ObjectsInFieldComponent;
  let fixture: ComponentFixture<ObjectsInFieldComponent>;

  beforeEach(async () => {
    await MockBuilder(ObjectsInFieldComponent, AppModule);
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ObjectsInFieldComponent);
    component = fixture.componentInstance;
    component.solution = SolutionGenerator.solution();
    fixture.detectChanges();
  });

  it("should create", () => {
    expect(component).toBeTruthy();
  });
});
