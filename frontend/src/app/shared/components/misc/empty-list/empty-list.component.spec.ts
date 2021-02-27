import { AppModule } from "@app/app.module";
import { MockBuilder, MockRender } from "ng-mocks";
import { EmptyListComponent } from "./empty-list.component";

describe("EmptyListComponent", () => {
  let component: EmptyListComponent;

  beforeEach(async () => MockBuilder(EmptyListComponent, AppModule));
  beforeEach(() => (component = MockRender(EmptyListComponent).point.componentInstance));

  it("should create", () => {
    expect(component).toBeTruthy();
  });
});
