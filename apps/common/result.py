from rest_framework.response import Response


class Result:
    @staticmethod
    def success(data=None, message="Success", code=0):
        return Response({"code": code, "message": message, "data": data})

    @staticmethod
    def error(message="Error", code=500, status=None):
        return Response({"code": code, "message": message, "data": None}, status=status or 200)