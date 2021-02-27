import { ComponentFixture, TestBed } from "@angular/core/testing";
import { AppModule } from "@app/app.module";
import { initialState } from "@app/store/state";
import { provideMockStore } from "@ngrx/store/testing";
import { MockBuilder } from "ng-mocks";
import { TelescopeComponent } from "./telescope.component";

describe("TelescopeComponent", () => {
  let component: TelescopeComponent;
  let fixture: ComponentFixture<TelescopeComponent>;

  beforeEach(async () => {
    await MockBuilder(TelescopeComponent, AppModule).provide(provideMockStore({ initialState }));
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(TelescopeComponent);
    component = fixture.componentInstance;
    component.id = 1;
    fixture.detectChanges();
  });

  it("should create", () => {
    expect(component).toBeTruthy();
  });
});
