import { HttpClientModule } from "@angular/common/http";
import { HttpClientTestingModule, HttpTestingController } from "@angular/common/http/testing";
import { TestBed } from "@angular/core/testing";
import { AppModule } from "@app/app.module";
import { SolutionGenerator } from "@shared/generators/solution.generator";
import { SolutionApiService } from "@shared/services/api/classic/platesolving/solution/solution-api.service";
import { MockBuilder } from "ng-mocks";

describe("SolutionApiService", () => {
  let service: SolutionApiService;
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await MockBuilder(SolutionApiService, AppModule).replace(HttpClientModule, HttpClientTestingModule);

    service = TestBed.inject(SolutionApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it("should be created", () => {
    expect(service).toBeTruthy();
  });

  it("getSolution should work", () => {
    const solution = SolutionGenerator.solution();

    service.getSolution(solution.content_type, solution.object_id).subscribe(response => {
      expect(response.id).toEqual(solution.id);
    });

    const req = httpMock.expectOne(
      `${service.configUrl}/?content_type=${solution.content_type}&object_id=${solution.object_id}`
    );
    expect(req.request.method).toBe("GET");
    req.flush(solution);
  });

  it("getSolutions should work", () => {
    const solutions = [SolutionGenerator.solution({ id: 1 }), SolutionGenerator.solution({ id: 2 })];

    service.getSolutions(solutions[0].content_type, ["1", "2"]).subscribe(response => {
      expect(response[0].id).toEqual(solutions[0].id);
      expect(response[1].id).toEqual(solutions[1].id);
    });

    const req = httpMock.expectOne(`${service.configUrl}/?content_type=${solutions[0].content_type}&object_ids=1,2`);
    expect(req.request.method).toBe("GET");
    req.flush(solutions);
  });
});
