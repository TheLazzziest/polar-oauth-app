import respx
from httpx import Response

from src.clients.polar.client import PolarClient
from src.clients.polar.contexts import ListExercisesContext
from src.clients.polar.models import Exercise


@respx.mock(assert_all_mocked=False)
async def test_list_exercises_statically(test_polar_client: PolarClient):
    """Tests the statically defined `list_exercises` method."""
    mock_response = [
        {
            "polar_user": "123",
            "start_time": "2023-01-01T10:00:00Z",
            "start_time_utc_offset": 0,
            "duration": "PT1H",
            "distance": 5000,
            "calories": 300,
            "device": "Polar Vantage V2",
            "has_route": True,
            "has_manual_lap": False,
            "sport": "RUNNING",
        }
    ]
    # Mock the API endpoint
    list_exercises_route = respx.get("/v3/exercises").mock(
        return_value=Response(200, json=mock_response)
    )

    # Call the client method
    exercises = await test_polar_client.list_exercises(context=ListExercisesContext())

    assert list_exercises_route.called
    assert isinstance(exercises, list)
    assert len(exercises) == 1
    assert isinstance(exercises[0], Exercise)
    assert exercises[0].sport == "RUNNING"


# @respx.mock
# async def test_get_exercise_dynamically(test_polar_client: PolarClient):
#     """
#     Tests the client's dynamic dispatch by
#     calling an endpoint via its method and path.
#     """
#     mock_response = {
#         "polar_user": "123",
#         "start_time": "2023-01-02T12:00:00Z",
#         "start_time_utc_offset": 0,
#         "duration": "PT2H",
#         "distance": 10000,
#         "calories": 600,
#         "device": "Polar Vantage V2",
#         "has_route": False,
#         "has_manual_lap": False,
#         "sport": "CYCLING",
#     }
#     get_exercise_route = respx.get("/v3/exercises/456").mock(
#         return_value=Response(200, json=mock_response)
#     )

#     exercise = await test_polar_client(
#   "GET", "/v3/exercises/{exercise_id}", exercise_id="456"
# )

#     assert get_exercise_route.called
#     assert isinstance(exercise, Exercise)
#     assert exercise.sport == "CYCLING"
#     assert exercise.distance == 10000


# @respx.mock
# async def test_get_exercise_gpx_format(test_polar_client: PolarClient):
#     """Tests fetching an exercise in GPX format."""
#     mock_gpx_content = """<?xml version="1.0" encoding="UTF-8"?>
# <gpx version="1.1" creator="Polar Flow">
#   <metadata><time>2023-01-01T10:00:00Z</time></metadata>
#   <trk>
#     <name>Running</name>
#     <trkseg>
#       <trkpt lat="60.123" lon="24.456">
#           <ele>50</ele>
#           <time>2023-01-01T10:00:05Z</time>
#       </trkpt>
#     </trkseg>
#   </trk>
# </gpx>"""

#     get_gpx_route = respx.get("/v3/exercises/789/gpx").mock(
#         return_value=Response(
#             200,
#             content=mock_gpx_content,
#             headers={"Content-Type": "application/gpx+xml"},
#         )
#     )

#     gpx_data = await test_polar_client.get_exercise(exercise_id="789", format="gpx")

#     assert get_gpx_route.called
#     assert isinstance(gpx_data, GPX)
#     assert gpx_data.tracks[0].name == "Running"
#     assert gpx_data.tracks[0].segments[0].points[0].latitude == 60.123


# @respx.mock(assert_all_mocked=False)
# async def test_get_exercise_tcx_format(test_polar_client: PolarClient):
#     """Tests fetching an exercise in TCX format."""
#     mock_tcx_content = """<?xml version="1.0" encoding="UTF-8"?>
# <TrainingCenterDatabase xmlns="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2">
#   <Activities>
#     <Activity Sport="Running">
#       <Id>2023-01-01T10:00:00.000Z</Id>
#       <Lap StartTime="2023-01-01T10:00:00.000Z">
#         <TotalTimeSeconds>3600.0</TotalTimeSeconds>
#         <DistanceMeters>5000.0</DistanceMeters>
#         <Calories>300</Calories>
#       </Lap>
#     </Activity>
#   </Activities>
# </TrainingCenterDatabase>"""

#     get_tcx_route = respx.get("/v3/exercises/101/tcx").mock(
#         return_value=Response(
#             200, content=mock_tcx_content, headers={
#           "Content-Type": "application/vnd.garmin.tcx+xml"
#         }
#         )
#     )

#     tcx_data = await test_polar_client.get_exercise(exercise_id="101", format="tcx")

#     assert get_tcx_route.called
#     assert isinstance(tcx_data, TCXExercise)
#     assert tcx_data.activity_type == "Running"
#     assert tcx_data.calories == 300
