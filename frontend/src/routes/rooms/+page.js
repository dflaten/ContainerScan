export async function load({ parent }) {
  const parentData = await parent();

  return {
    rooms: parentData.rooms
  };
}
